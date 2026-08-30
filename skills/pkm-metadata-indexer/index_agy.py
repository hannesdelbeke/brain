"""Index Antigravity CLI (`agy`) conversations with the vault indexer.

The second scanner over the `collect=` contract, after `index_sessions.py`. It
exists to prove the seam is real: Claude Code writes append-only JSONL and is
resumed by byte offset, agy writes one SQLite database per conversation whose
step payloads are binary protobuf with no schema shipped anywhere, and both
arrive as `(notes, sections, links, errors)`.

    python index_agy.py --root ~/.gemini/antigravity-cli
    python index_agy.py --probe          # what the payload fields hold, per step type
    python index_agy.py --selfcheck
    python searchd.py --corpus index_agy.py:scan_agy=agy=~/.gemini/antigravity-cli

A conversation is a document, a step is a section, and every file a tool touched
is an edge, the same shape `index_sessions.py` produces.

The payload is read by walking protobuf wire format without a `.proto`: field
number and wire type come off the varint key, a length-delimited chunk is a
nested message when it parses as one and a string when it decodes as printable
UTF-8. Prose is taken from the field paths in `PROSE_FIELDS`, which were found by
volume with `--probe` and are asserted by `--selfcheck`; tool calls are found by
content instead, since agy writes their arguments as a JSON object and a JSON
object is recognisable wherever the field numbers move to.

Only prose and whitelisted tool arguments are indexed, for the reason
`index_sessions.py` skips tool results: they are most of the bytes, they hold
credentials and whole-file dumps, and what they read is still on disk.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import index_pkm_meta as pkm

# Step types carrying a turn. Everything else is a tool call, a retry, or client
# machinery, and is only indexed if it holds a tool-argument JSON object.
ROLES = {14: "user", 15: "assistant"}
# Where the prose sits, by step type, as `field.field` from the payload root.
# agy repeats each turn under a second path (19.3.1, 20.8); duplicates collapse
# before this is consulted, so only the first path needs to be listed. 20.3 is
# the assistant's thinking and is skipped, as it is in `index_sessions.py`.
PROSE_FIELDS = {14: {"19.2"}, 15: {"20.1"}}
# Tool arguments by whitelist: what makes "which conversation ran that command"
# answerable, without pasting a file back into the index. `CodeContent` and
# `ReplacementContent` are the whole-file arguments and are deliberately absent.
TOOL_ARG_KEYS = ("toolAction", "toolSummary", "CommandLine", "Query", "AbsolutePath",
                 "SearchPath", "DirectoryPath", "Cwd", "Url", "TaskId", "Action")
TOOL_ARG_CHARS = 300
# Arguments naming a file on disk, which become edges.
FILE_ARG_KEYS = ("AbsolutePath", "DirectoryPath", "SearchPath")
MIN_PROSE_CHARS = 30
MIN_USER_PROSE_CHARS = 10
TITLE_CHARS = 80
SNIPPET_CHARS = 240
MAX_DEPTH = 8

STATE_NAME = ".pkm_agy_state.json"


def varint(data: bytes, i: int) -> tuple[int, int]:
    shift = value = 0
    while i < len(data):
        byte = data[i]
        i += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, i
        shift += 7
    raise ValueError("truncated varint")


def printable(chunk: bytes) -> str | None:
    """The chunk as text, when it is text rather than a packed message."""
    try:
        text = chunk.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text:
        return None
    clean = sum(character.isprintable() or character in "\n\t" for character in text)
    return text if clean / len(text) > 0.95 else None


def walk(data: bytes, path: str = "", depth: int = 0, out: list | None = None) -> list:
    """Every string in a protobuf message, as `(field path, text)`, without a schema.

    A length-delimited chunk is ambiguous on the wire: a nested message, a string
    and a byte array are the same three bytes of header. It is treated as a
    message when it parses as one and as a string otherwise, and when it does
    both, both are kept, since a JSON argument blob parses as a message by
    coincidence often enough to lose it that way.
    """
    if out is None:
        out = []
    i = 0
    while i < len(data):
        try:
            key, i = varint(data, i)
        except ValueError:
            return out
        field, wire = key >> 3, key & 7
        here = f"{path}.{field}" if path else str(field)
        if wire == 0:
            try:
                _, i = varint(data, i)
            except ValueError:
                return out
        elif wire == 1:
            i += 8
        elif wire == 5:
            i += 4
        elif wire == 2:
            try:
                length, i = varint(data, i)
            except ValueError:
                return out
            chunk, i = data[i:i + length], i + length
            if len(chunk) < length:
                return out
            nested = []
            if depth < MAX_DEPTH and chunk:
                try:
                    nested = walk(chunk, here, depth + 1, [])
                except Exception:
                    nested = []
            text = printable(chunk)
            if nested:
                out.extend(nested)
            if text is not None and (not nested or text.lstrip().startswith("{")):
                out.append((here, text))
        else:  # an unknown wire type means the parse has gone off the rails
            return out
    return out


def json_object(text: str) -> dict | None:
    if not text.lstrip().startswith("{"):
        return None
    try:
        value = json.loads(text)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


@dataclass(frozen=True)
class Event:
    idx: int
    role: str
    text: str
    files: tuple[str, ...] = ()


def events_for(idx: int, step_type: int, payload: bytes):
    """The indexable events in one step: at most one turn, plus its tool calls."""
    seen = set()
    strings = []
    for field, text in walk(payload or b""):
        if text in seen:
            continue
        seen.add(text)
        strings.append((field, text))

    role = ROLES.get(step_type)
    prose_fields = PROSE_FIELDS.get(step_type, set())
    for field, text in strings:
        arguments = json_object(text)
        if arguments is not None:
            parts = [f"{key}: {str(arguments[key])[:TOOL_ARG_CHARS]}"
                     for key in TOOL_ARG_KEYS if arguments.get(key)]
            if parts:
                files = tuple(str(arguments[key]) for key in FILE_ARG_KEYS if arguments.get(key))
                yield Event(idx, "tool", " ".join(parts), files)
            continue
        if role is None or field not in prose_fields:
            continue
        text = text.strip()
        floor = MIN_USER_PROSE_CHARS if role == "user" else MIN_PROSE_CHARS
        if len(text) >= floor:
            yield Event(idx, role, text)


def read_steps(db_path: Path, after: int = -1):
    """Steps in order, read-only so a live conversation is not disturbed."""
    connection = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=30.0)
    try:
        return connection.execute(
            "SELECT idx, step_type, step_payload FROM steps WHERE idx >= ? ORDER BY idx",
            (after + 1,)).fetchall()
    finally:
        connection.close()


def step_count(db_path: Path) -> tuple[int, int]:
    connection = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=30.0)
    try:
        total, highest = connection.execute(
            "SELECT count(*), coalesce(max(idx), -1) FROM steps").fetchone()
        return total, highest
    finally:
        connection.close()


def read_history(root: Path) -> dict:
    """`conversationId` to its first prompt and workspace, from agy's prompt history.

    Optional: the file only covers conversations started from the directory it
    was written in, and a conversation missing from it takes its title from its
    own first user turn.
    """
    history = {}
    path = root / "history.jsonl"
    if not path.exists():
        return history
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        conversation = record.get("conversationId")
        if conversation and conversation not in history and record.get("type") != "slash_command":
            history[conversation] = record
    return history


def scan_conversation(db_path: Path, relative_path: str, meta: dict, resume=None):
    """Return the note row, its sections, its edges and the last step read.

    `resume` is `(cursor, note, sections, links)` from the last run. Steps only
    ever get appended, so the tail read is `idx >= cursor`: the last step is
    reread because agy updates it in place while it streams, and the rows it
    produced last time are dropped first so the reread replaces them.
    """
    cursor, cached_note, cached_sections, cached_links = resume or (0, None, [], [])
    sections = [section for section in cached_sections if section.start_line < cursor]
    links = [link for link in cached_links if link.start_line < cursor]
    linked_files = {link.raw_target for link in links}
    title = (cached_note[1] if cached_note else "") or ""
    snippet = cached_note[7] if cached_note else ""
    words = cached_note[8] if cached_note else 0
    highest = cursor - 1

    for idx, step_type, payload in read_steps(db_path, cursor - 1):
        highest = max(highest, idx)
        # One step can hold a turn and the tool call it made, so the section id
        # carries the event as well as the step, or the second would overwrite
        # the first through its primary key and be counted but never stored.
        for event_index, event in enumerate(events_for(idx, step_type, payload)):
            if event.role == "user":
                title = title or " ".join(event.text.split())[:TITLE_CHARS]
                snippet = snippet or " ".join(event.text.split())[:SNIPPET_CHARS]
            words += len(event.text.split())
            heading = title or db_path.stem
            for chunk_index, chunk_text in enumerate(
                pkm.chunk_section(heading, f"{event.role}: {event.text}")
            ):
                sections.append(pkm.Section(
                    section_id=f"{relative_path}::{idx}:{event_index}:{chunk_index}",
                    path=relative_path,
                    heading=heading,
                    start_line=idx,
                    chunk_index=chunk_index,
                    sha256=pkm.get_sha256(chunk_text),
                    text=chunk_text,
                ))
            for file_path in event.files:
                if file_path not in linked_files:
                    linked_files.add(file_path)
                    links.append(pkm.Link(relative_path, file_path, None, idx))

    if not sections:
        return None, [], [], highest + 1
    title = title or " ".join((meta.get("display") or db_path.stem).split())[:TITLE_CHARS]
    snippet = snippet or title
    workspace = meta.get("workspace") or ""
    note = (
        relative_path,
        title,
        Path(workspace).name or "agy",
        None,
        None,
        json.dumps([]),
        json.dumps(["session", "agy"]),
        snippet,
        words,
    )
    return note, sections, links, highest + 1


def scanner_fingerprint() -> str:
    """Any change to the parsing invalidates every cursor, since old rows would survive it."""
    return hashlib.sha256(Path(__file__).read_bytes()
                          + pkm.CHUNKING_VERSION.encode()).hexdigest()[:16]


def read_state(state_file: Path) -> dict:
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return state.get("files", {}) if state.get("scanner") == scanner_fingerprint() else {}


def scan_agy(root: Path, db_path: Path | None = None, resume: bool = True):
    """Scanner with the same contract as `collect_index_data`."""
    root = Path(root)
    state_file = root / STATE_NAME
    previous = read_state(state_file) if resume else {}
    import index_sessions
    cache = index_sessions.cached_rows(
        Path(db_path) if db_path else pkm.default_db_path(root)) if previous else {}
    history = read_history(root)

    notes, sections, links, errors, state = [], [], [], [], {}
    for conversation in sorted(root.glob("conversations/*.db")):
        relative_path = conversation.relative_to(root).as_posix()
        try:
            entry = previous.get(relative_path)
            cached = cache.get(relative_path)
            # Fewer rows in the index than the cursor accounts for means the last
            # run died before writing them, so the cursor cannot be trusted.
            if cached and entry and len(cached[1]) != entry["sections"]:
                cached = None
            start = None
            if cached and entry:
                total, highest = step_count(conversation)
                if total >= entry["steps"] and highest >= entry["cursor"] - 1:
                    start = (entry["cursor"], *cached)
            meta = history.get(conversation.stem, {})
            note, note_sections, note_links, cursor = scan_conversation(
                conversation, relative_path, meta, start)
        except Exception as error:  # one unreadable conversation must not fail the run
            errors.append((relative_path, "parse", str(error)))
            continue
        if note is None:
            continue
        state[relative_path] = {
            "cursor": cursor,
            "steps": step_count(conversation)[0],
            "sections": len(note_sections),
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


def probe(root: Path, limit: int = 6):
    """Print which payload field holds what, per step type, ranked by volume.

    `PROSE_FIELDS` was read off this output and will need rereading if agy
    changes its payload: the prose field for a step type is the one whose sample
    is a sentence rather than a path, an id or a JSON blob.
    """
    volume = collections.defaultdict(collections.Counter)
    sample, counts = collections.defaultdict(dict), collections.Counter()
    for conversation in sorted(Path(root).glob("conversations/*.db")):
        try:
            rows = read_steps(conversation)
        except sqlite3.Error as error:
            print(f"skip {conversation.name}: {error}")
            continue
        for idx, step_type, payload in rows:
            counts[step_type] += 1
            for field, text in walk(payload or b""):
                if len(text) < 40:
                    continue
                volume[step_type][field] += len(text)
                sample[step_type].setdefault(field, " ".join(text.split())[:120])
    for step_type in sorted(volume):
        marks = "  <- prose" if step_type in PROSE_FIELDS else ""
        print(f"== step_type {step_type}: {counts[step_type]} steps{marks}")
        for field, total in volume[step_type].most_common(limit):
            flag = " *" if field in PROSE_FIELDS.get(step_type, ()) else "  "
            print(f" {flag}{field}: {total:,} chars | {sample[step_type][field]}")


def encode(field: int, value) -> bytes:
    """The two wire types this file reads, for building a payload in the selfcheck."""
    if isinstance(value, int):
        return varint_bytes(field << 3) + varint_bytes(value)
    body = value.encode("utf-8") if isinstance(value, str) else value
    return varint_bytes((field << 3) | 2) + varint_bytes(len(body)) + body


def varint_bytes(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def selfcheck():
    import tempfile

    prose = "index the antigravity transcripts as well, they are the second corpus"
    payload_user = encode(19, encode(2, prose) + encode(3, encode(1, prose)))
    reply = "I will add a scanner over the conversation databases and wire it to the daemon."
    payload_assistant = (
        encode(20, encode(1, reply) + encode(8, reply)
               + encode(3, "**Thinking**: the payload is protobuf with no schema shipped.")
               + encode(7, encode(3, json.dumps({
                   "CommandLine": "python index_agy.py --selfcheck",
                   "Cwd": "/w", "toolAction": "Run the selfcheck",
                   "CodeContent": "x" * 5000}))))
    )
    payload_tool = encode(5, encode(4, encode(3, json.dumps({
        "AbsolutePath": "/w/index_agy.py", "Query": "chunk_section"}))))

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "conversations").mkdir()
        conversation = "00000000-0000-0000-0000-000000000001"
        database = root / "conversations" / f"{conversation}.db"
        connection = sqlite3.connect(database)
        connection.execute("CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER,"
                           " step_payload BLOB)")
        connection.executemany("INSERT INTO steps VALUES (?, ?, ?)", [
            (0, 14, payload_user), (1, 15, payload_assistant), (2, 5, payload_tool)])
        connection.commit()
        connection.close()
        (root / "history.jsonl").write_text(json.dumps({
            "display": prose, "workspace": "C:\\w\\brain", "conversationId": conversation}) + "\n",
            encoding="utf-8")

        notes, sections, links, errors = scan_agy(root, resume=False)
        assert not errors, errors
        assert len(notes) == 1, notes
        note = notes[0]
        assert note[0] == f"conversations/{conversation}.db"
        assert note[1] == prose[:TITLE_CHARS], note[1]
        assert note[2] == "brain", "the workspace names the category"
        assert json.loads(note[6]) == ["session", "agy"], note[6]

        texts = [section.text for section in sections]
        joined = "\n".join(texts)
        assert any(f"user: {prose}" in text for text in texts), texts
        assert any(f"assistant: {reply}" in text for text in texts), texts
        assert sum(f"user: {prose}" in text for text in texts) == 1, \
            "a turn repeated under a second field path is one section"
        assert "Thinking" not in joined, "thinking is skipped"
        assert "xxxxx" not in joined, "a whole-file argument is not indexed"
        assert "CommandLine: python index_agy.py --selfcheck" in joined, "tool arguments are indexed"
        assert "Query: chunk_section" in joined, "a tool step is indexed"
        assert "CodeContent" not in joined, "an argument outside the whitelist is dropped"
        assert {section.start_line for section in sections} == {0, 1, 2}, \
            "a step is a section, addressed by its index"
        assert len({section.section_id for section in sections}) == len(sections), \
            "a step holding a turn and a tool call is two sections, not one overwriting the other"
        assert sum(section.start_line == 1 for section in sections) == 2, \
            "the assistant turn and the command it ran are both indexed"

        edges = {(link.source_path, link.raw_target) for link in links}
        assert (f"conversations/{conversation}.db", "/w/index_agy.py") in edges, edges
        assert len(edges) == len(links), "no duplicate edge from one path seen twice"

        # The tail read, against a real index: the rows for the steps already
        # read come back out of the database and only the new step is parsed.
        index = root / "index.db"
        pkm.build_index(vault_path=str(root), db_path=str(index), skip_embeddings=True,
                        collect=lambda scanned: scan_agy(scanned, index))
        connection = sqlite3.connect(database)
        connection.execute("INSERT INTO steps VALUES (3, 14, ?)",
                           (encode(19, encode(2, "and a second question about the resume path")),))
        connection.commit()
        connection.close()

        resumed, sections, links, errors = scan_agy(root, index)
        assert not errors, errors
        assert len(sections) == len(texts) + 1, "one new step, one new section"
        assert any("resume path" in section.text for section in sections), "the new step is read"
        assert any(f"user: {prose}" in section.text for section in sections), \
            "the steps already read come back from the index rather than being reparsed"
        assert resumed[0][8] > note[8], "the word count carries across a resume"

    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default="~/.gemini/antigravity-cli", help="agy state directory")
    parser.add_argument("--db", default=None, help="Database, otherwise <root>/.pkm_index.db")
    parser.add_argument("--with-embeddings", action="store_true", help="Embed as well as index")
    parser.add_argument("--full", action="store_true", help="Reparse every conversation")
    parser.add_argument("--probe", action="store_true",
                        help="Print the payload field map and exit, to check PROSE_FIELDS")
    parser.add_argument("--selfcheck", action="store_true", help="Run the assertions and exit")
    args = parser.parse_args()

    if args.selfcheck:
        selfcheck()
        return
    root = Path(args.root).expanduser().resolve()
    if args.probe:
        probe(root)
        return

    database = Path(args.db) if args.db else pkm.default_db_path(root)
    pkm.build_index(
        vault_path=str(root),
        db_path=str(database),
        skip_embeddings=not args.with_embeddings,
        collect=lambda scanned_root: scan_agy(scanned_root, database, resume=not args.full),
    )


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
