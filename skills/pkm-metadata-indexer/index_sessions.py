"""Index agent session transcripts with the vault indexer.

A transcript is a document, a turn is a section, and a subagent spawn is an edge
to the session that spawned it, so `build_index` stores sessions in the same
tables as markdown notes and `search_index` ranks both with no changes:

    python index_sessions.py --root ~/.claude/projects
    python searchd.py --vault brain=/path/to/brain --sessions claude=~/.claude/projects

Only prose and tool arguments are indexed. Tool results are 80% of the corpus by
size, they hold the API keys and the file dumps, and whatever they read is still
on disk and searchable in place. Thinking blocks are another 6% and are skipped
for now. That takes 1.49 GB to roughly 95 MB.
"""

from __future__ import annotations

import argparse
import json
import re
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


def iter_events(path: Path):
    """Yield indexable turns from one transcript, dropping repeats.

    Claude Code writes a line per content block and reuses `message.id` across
    them, so the same block appears more than once. Keying on the id and the text
    collapses that without holding the file in memory, which matters when the
    largest transcript here is 79 MB.
    """
    seen = set()
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line, raw in enumerate(handle, start=1):
            try:
                record = json.loads(raw)
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


def scan_transcript(path: Path, relative_path: str):
    """Return the note row, its sections and its edges for one transcript."""
    meta = agent_meta(path)
    parent = parent_transcript(relative_path)
    title = meta.get("description") or ""
    snippet = ""
    words = 0
    sections = []
    links = []
    linked_files = set()

    for event in iter_events(path):
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
        return None, [], []

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
    return note, sections, links


def scan_sessions(root: Path):
    """Scanner with the same contract as `collect_index_data`."""
    notes, sections, links, errors = [], [], [], []
    for path in transcript_paths(root):
        relative_path = path.relative_to(root).as_posix()
        try:
            note, note_sections, note_links = scan_transcript(path, relative_path)
        except Exception as error:  # one unreadable transcript must not fail the run
            errors.append((relative_path, "parse", str(error)))
            continue
        if note is None:
            continue
        notes.append(note)
        sections.extend(note_sections)
        links.extend(note_links)
    return notes, sections, links, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default="~/.claude/projects", help="Transcript root")
    parser.add_argument("--db", default=None, help="Database, otherwise <root>/.pkm_index.db")
    parser.add_argument("--with-embeddings", action="store_true",
                        help="Embed as well as index, roughly 3 minutes for the full corpus")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    pkm.build_index(
        vault_path=str(root),
        db_path=args.db or str(pkm.default_db_path(root)),
        skip_embeddings=not args.with_embeddings,
        collect=scan_sessions,
    )


if __name__ == "__main__":
    main()
