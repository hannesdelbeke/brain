"""Index agent session transcripts with the vault indexer.

A transcript is a document, a turn is a section, and a subagent spawn is an edge
to the session that spawned it, so `build_index` stores sessions in the same
tables as markdown notes and `search_index` ranks both with no changes:

    python index_sessions.py --root ~/.claude/projects
    python searchd.py --vault brain=/path/to/brain --sessions claude=~/.claude/projects

Reindexing is a tail read: a transcript is append-only, so each run remembers the
byte it stopped at and the next one parses only what was written since, taking
the rest of the rows back out of the index. `--full` reparses everything.

Only prose and tool arguments are indexed. Tool results are 80% of the corpus by
size, they hold the API keys and the file dumps, and whatever they read is still
on disk and searchable in place. Thinking blocks are another 6% and are skipped
for now. That takes 1.49 GB to roughly 95 MB.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import index_pkm_meta as pkm

# Tool inputs are indexed by whitelist. `command` and `file_path` are what makes
# "which session ran that migration" answerable, while `old_string` and friends
# would paste whole files back into the index for nothing.
TOOL_ARG_KEYS = ("description", "command", "file_path", "notebook_path", "path",
                 "pattern", "query", "url", "prompt", "subagent_type")
TOOL_ARG_CHARS = 300
FILE_ARG_KEYS = ("file_path", "notebook_path")
# "yes", "continue" and "do it" cost a vector and return nothing.
MIN_PROSE_CHARS = 30
# The client writes slash commands, hook output and its own notifications into
# the transcript as user turns. They are the loudest thing in the file and none
# of it was said by anyone, so it is dropped before it can become a title.
SYNTHETIC_PROSE = re.compile(
    r"^<(local-command|command-(name|message|args|contents|stdout|stderr)"
    r"|bash-(input|stdout|stderr)|task-notification|system-reminder|user-prompt-submit-hook)"
)
TITLE_CHARS = 80
SNIPPET_CHARS = 240

# A transcript is append-only, so the bytes already read never change and the
# next run can start where the last one stopped. What was read is remembered
# here, one entry per transcript; the rows themselves are read back out of the
# index, so no text is stored twice.
STATE_NAME = ".pkm_scan_state.json"
# Enough of the bytes before the offset to notice a transcript that was rewritten
# rather than appended to. Hashing the whole prefix would cost the read the
# offset exists to avoid.
PREFIX_BYTES = 4096


@dataclass(frozen=True)
class Event:
    line: int
    role: str
    text: str
    files: tuple[str, ...] = ()


def event_for(role: str, block, line: int) -> Event | None:
    """Turn one content block into an indexable event, or None to skip it."""
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind == "text":
        text = (block.get("text") or "").strip()
        if len(text) < MIN_PROSE_CHARS or SYNTHETIC_PROSE.match(text):
            return None
        return Event(line, role, text)
    if kind == "tool_use":
        arguments = block.get("input") or {}
        if not isinstance(arguments, dict):
            return None
        parts = [f"{key}: {str(arguments[key])[:TOOL_ARG_CHARS]}"
                 for key in TOOL_ARG_KEYS if arguments.get(key)]
        files = tuple(str(arguments[key]) for key in FILE_ARG_KEYS if arguments.get(key))
        return Event(line, "tool", " ".join([str(block.get("name") or "tool"), *parts]), files)
    return None


def iter_events(path: Path, start_offset: int = 0, start_line: int = 0, position: dict | None = None):
    """Yield indexable turns from one transcript, dropping repeats.

    Claude Code writes a line per content block and reuses `message.id` across
    them, so the same block appears more than once. Keying on the id and the text
    collapses that without holding the file in memory, which matters when the
    largest transcript here is 79 MB.

    The file is read as bytes so the offset is exact: reading resumes at
    `start_offset`, counting from `start_line`, and `position` reports where it
    stopped. A last line with no newline is still being written, so it is left
    for the next run rather than half indexed.
    """
    seen = set()
    line = start_line
    offset = start_offset
    with path.open("rb") as handle:
        handle.seek(offset)
        for raw in handle:
            if not raw.endswith(b"\n"):
                break
            line += 1
            offset += len(raw)
            try:
                record = json.loads(raw.decode("utf-8", errors="ignore"))
            except ValueError:
                continue
            role = record.get("type")
            if role not in ("user", "assistant") or record.get("isMeta"):
                continue
            message = record.get("message") or {}
            if not isinstance(message, dict):
                continue
            message_id = message.get("id") or record.get("uuid") or ""
            content = message.get("content")
            blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content or []
            for block in blocks:
                event = event_for(role, block, line)
                if event is None:
                    continue
                key = (message_id, event.text)
                if key in seen:
                    continue
                seen.add(key)
                yield event
    if position is not None:
        position.update(offset=offset, line=line)


def transcript_paths(root: Path) -> list[Path]:
    """Main sessions live beside their project slug, subagents one level in."""
    return sorted(root.glob("*/*.jsonl")) + sorted(root.glob("*/*/subagents/*.jsonl"))


def parent_transcript(relative_path: str) -> str | None:
    """`slug/<uuid>/subagents/agent-x.jsonl` was spawned by `slug/<uuid>.jsonl`."""
    parts = relative_path.split("/")
    return f"{parts[0]}/{parts[1]}.jsonl" if len(parts) == 4 and parts[2] == "subagents" else None


def agent_meta(path: Path) -> dict:
    meta_file = path.with_suffix(".meta.json")
    if not meta_file.exists():
        return {}
    try:
        return json.loads(meta_file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def scan_transcript(path: Path, relative_path: str, resume=None):
    """Return the note row, its edges, its sections and where reading stopped.

    `resume` is `(offset, line, note, sections, links)` from the last run, which
    makes this a tail read: the rows already built are kept and only the bytes
    appended since are parsed. The repeat filter only spans one call, so a block
    split across the boundary can be indexed twice; it costs one section.
    """
    offset, first_line, cached_note, cached_sections, cached_links = resume or (0, 0, None, [], [])
    meta = agent_meta(path)
    parent = parent_transcript(relative_path)
    title = (cached_note[1] if cached_note else "") or meta.get("description") or ""
    snippet = cached_note[7] if cached_note else ""
    words = cached_note[8] if cached_note else 0
    sections = list(cached_sections)
    # The parent edge is appended after the loop, so it must not be carried in twice.
    links = [link for link in cached_links if link.raw_target != parent]
    linked_files = {link.raw_target for link in links}
    position = {"offset": offset, "line": first_line}

    for event in iter_events(path, offset, first_line, position):
        if not title and event.role == "user":
            title = " ".join(event.text.split())[:TITLE_CHARS]
        if not snippet and event.role == "user":
            snippet = " ".join(event.text.split())[:SNIPPET_CHARS]
        words += len(event.text.split())
        # The heading rides along into every chunk, so it carries the session
        # subject into turns that never restate it.
        heading = title or path.stem
        for chunk_index, chunk_text in enumerate(
            pkm.chunk_section(heading, f"{event.role}: {event.text}")
        ):
            sections.append(
                pkm.Section(
                    section_id=f"{relative_path}::{event.line}:{chunk_index}",
                    path=relative_path,
                    heading=heading,
                    start_line=event.line,
                    chunk_index=chunk_index,
                    sha256=pkm.get_sha256(chunk_text),
                    text=chunk_text,
                )
            )
        for file_path in event.files:
            if file_path not in linked_files:
                linked_files.add(file_path)
                links.append(pkm.Link(relative_path, file_path, None, event.line))

    if parent:
        links.append(pkm.Link(relative_path, parent, parent, 0))
    if not sections:
        return None, [], [], position

    tags = ["session"] + (["subagent", meta["agentType"]] if meta.get("agentType") else [])
    note = (
        relative_path,
        title or path.stem,
        relative_path.split("/")[0],
        None,
        None,
        json.dumps([]),
        json.dumps(tags),
        snippet,
        words,
    )
    return note, sections, links, position


def scanner_fingerprint() -> str:
    """Invalidate every offset when the parsing changes, since old rows would survive it."""
    source = Path(__file__).read_bytes()
    return hashlib.sha256(source + pkm.CHUNKING_VERSION.encode()).hexdigest()[:16]


def read_state(state_file: Path) -> dict:
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return state.get("files", {}) if state.get("scanner") == scanner_fingerprint() else {}


def prefix_matches(handle, entry: dict) -> bool:
    """Cheap check that the bytes before the offset are the ones that were read."""
    start = max(0, entry["offset"] - PREFIX_BYTES)
    handle.seek(start)
    return hashlib.sha256(handle.read(entry["offset"] - start)).hexdigest() == entry["prefix"]


def prefix_hash(path: Path, offset: int) -> str:
    with path.open("rb") as handle:
        handle.seek(max(0, offset - PREFIX_BYTES))
        return hashlib.sha256(handle.read(min(offset, PREFIX_BYTES))).hexdigest()


def cached_rows(database: Path) -> dict:
    """Read the last run's rows back out of the index, keyed by transcript.

    The index already holds every section with its text, so a transcript that
    did not change needs neither a reparse nor a second copy on disk. A section
    whose text is missing drops its whole transcript back to a full read.
    """
    if not database.exists():
        return {}
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=60.0)
    try:
        text_by_id = dict(connection.execute("SELECT section_id, content FROM sections_fts"))
        rows = {
            note[0]: [tuple(note), [], []]
            for note in connection.execute(
                "SELECT path, filename, category, energy, sentiment, sentiment_labels,"
                " tags, summary_snippet, word_count FROM notes"
            )
        }
        for section_id, path, heading, start_line, chunk_index, sha256 in connection.execute(
            "SELECT id, path, heading, start_line, chunk_index, sha256 FROM sections"
            " ORDER BY path, start_line, chunk_index"
        ):
            row = rows.get(path)
            if row is None:
                continue
            text = text_by_id.get(section_id)
            if text is None:
                rows.pop(path)
                continue
            row[1].append(pkm.Section(section_id=section_id, path=path, heading=heading,
                                      start_line=start_line, chunk_index=chunk_index,
                                      sha256=sha256, text=text))
        for link in connection.execute(
            "SELECT source_path, raw_target, resolved_target_path, start_line FROM edges"
        ):
            row = rows.get(link[0])
            if row is not None:
                row[2].append(pkm.Link(*link))
        return {path: row for path, row in rows.items() if row[1]}
    except sqlite3.Error:  # a half-built or foreign index is just a cache miss
        return {}
    finally:
        connection.close()


def scan_sessions(root: Path, db_path: Path | None = None, resume: bool = True):
    """Scanner with the same contract as `collect_index_data`.

    Transcripts only ever grow, so a run reparses the bytes appended since the
    last one and takes the rest of the rows from the index. A transcript that
    shrank, or whose bytes before the offset no longer hash the same, was not
    appended to and is read in full.
    """
    state_file = root / STATE_NAME
    previous = read_state(state_file) if resume else {}
    cache = cached_rows(Path(db_path) if db_path else pkm.default_db_path(root)) if previous else {}

    notes, sections, links, errors, state = [], [], [], [], {}
    for path in transcript_paths(root):
        relative_path = path.relative_to(root).as_posix()
        try:
            stat = path.stat()
            entry = previous.get(relative_path)
            cached = cache.get(relative_path)
            # Fewer rows in the index than the offset accounts for means the last
            # run died before writing them, so the offset cannot be trusted.
            if cached and entry and len(cached[1]) != entry["sections"]:
                cached = None
            if cached and entry and entry["size"] == stat.st_size and entry["mtime"] == stat.st_mtime_ns:
                note, note_sections, note_links = cached
                position = {"offset": entry["offset"], "line": entry["line"]}
            else:
                start = None
                if cached and entry and stat.st_size > entry["size"]:
                    with path.open("rb") as handle:
                        if prefix_matches(handle, entry):
                            start = (entry["offset"], entry["line"], *cached)
                note, note_sections, note_links, position = scan_transcript(path, relative_path, start)
        except Exception as error:  # one unreadable transcript must not fail the run
            errors.append((relative_path, "parse", str(error)))
            continue
        if note is None:
            continue
        state[relative_path] = {
            "size": stat.st_size, "mtime": stat.st_mtime_ns,
            "offset": position["offset"], "line": position["line"],
            "sections": len(note_sections),
            "prefix": entry["prefix"] if position["offset"] == (entry or {}).get("offset")
            else prefix_hash(path, position["offset"]),
        }
        notes.append(note)
        sections.extend(note_sections)
        links.extend(note_links)

    try:
        state_file.write_text(json.dumps({"scanner": scanner_fingerprint(), "files": state}),
                              encoding="utf-8")
    except OSError as error:  # a read-only corpus still indexes, it just cannot resume
        errors.append((STATE_NAME, "state", str(error)))
    return notes, sections, links, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default="~/.claude/projects", help="Transcript root")
    parser.add_argument("--db", default=None, help="Database, otherwise <root>/.pkm_index.db")
    parser.add_argument("--with-embeddings", action="store_true",
                        help="Embed as well as index, roughly 3 minutes for the full corpus")
    parser.add_argument("--full", action="store_true",
                        help="Reparse every transcript instead of resuming at the last offset")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    database = Path(args.db) if args.db else pkm.default_db_path(root)
    pkm.build_index(
        vault_path=str(root),
        db_path=str(database),
        skip_embeddings=not args.with_embeddings,
        collect=lambda scanned_root: scan_sessions(scanned_root, database, resume=not args.full),
    )


if __name__ == "__main__":
    main()
