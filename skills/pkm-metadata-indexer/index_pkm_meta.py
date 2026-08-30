"""Local metadata, section, link, and hybrid search index for a Markdown vault."""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from fastembed import TextEmbedding

    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False


def get_embedding_providers() -> list[str]:
    if not HAS_FASTEMBED:
        return ["CPUExecutionProvider"]
    try:
        import onnxruntime as ort
        available = set(ort.get_available_providers())
        providers = [p for p in ["CUDAExecutionProvider", "DmlExecutionProvider", "CPUExecutionProvider"] if p in available]
        return providers or ["CPUExecutionProvider"]
    except Exception:
        return ["CPUExecutionProvider"]


EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSIONS = 384
CHUNKING_VERSION = "heading-estimate-v1"
MAX_CHUNK_ESTIMATED_TOKENS = 360
CHUNK_OVERLAP_ESTIMATED_TOKENS = 40
SCHEMA_VERSION = "2"
IGNORED_DIRS = {".obsidian", ".git", ".trash", "node_modules", ".venv", "__pycache__"}
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)

# Encoding one short query is dispatch-bound, not compute-bound. Measured on this
# machine: 57-100ms per query on DirectML against 4-38ms on CPU, because a batch of
# one never fills the GPU. Bulk indexing keeps the GPU, where batches are large and
# DirectML runs at 165 vec/s. Set to None to use whatever provider indexing uses.
QUERY_PROVIDERS = ["CPUExecutionProvider"]

# One intra-op thread on the query path. Measured on a 12-core laptop encoding
# one string every 250ms, the way searchd's keepalive does: the default pool
# busy-spins 11.93 cores, threads=2 burns 0.96, threads=1 burns 0.05. A query
# encode goes 3.8ms to 8.6ms in exchange, invisible inside a 13-22ms query.
# Indexing leaves threads unset, where the pool is doing real parallel work.
QUERY_THREADS = 1

# A cross-encoder reads the query and one section together instead of comparing
# two vectors made apart, which is the standard accuracy step after fusion. It
# ships with fastembed, so it costs no new dependency, and it is off by default
# because it costs time: about 22ms per candidate on this machine, so 227ms over
# 10, 533ms over 20 and 706ms over 30, against a 26ms query. Twenty is the
# default because the sections that answered the sample query sat at fused rank
# 9 and 11, so a top-10 rerank would have found one of them and missed the other.
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
RERANK_CANDIDATES = 20

_MODEL_CACHE: dict[tuple, object] = {}
_RERANK_CACHE: dict[str, object] = {}
# searchd answers queries on several threads, and a model that is loaded lazily
# would otherwise be loaded once per thread that asked first: a second 90 MB
# download and a second ONNX session for nothing. Only the load is guarded, the
# models themselves are called concurrently and onnxruntime allows that.
_LOAD_LOCK = threading.Lock()


def get_embedding_model(providers: list[str] | None = None, threads: int | None = None):
    """Load the embedding model once per process.

    Loading costs about 2.9s and encoding one query costs milliseconds, so a
    long-lived process (searchd.py) must never pay that twice. A one-shot CLI
    call is unaffected, it only ever asks once.

    `threads` caps the ONNX Runtime intra-op pool. Leave it None for bulk
    embedding and pass QUERY_THREADS on the query path, see the note above.
    """
    key = (tuple(providers or get_embedding_providers()), threads)
    with _LOAD_LOCK:
        if key not in _MODEL_CACHE:
            kwargs = {"threads": threads} if threads is not None else {}
            _MODEL_CACHE[key] = TextEmbedding(model_name=EMBEDDING_MODEL, providers=list(key[0]), **kwargs)
    return _MODEL_CACHE[key]


def get_cross_encoder():
    """Load the reranking model once per process, on first use.

    Loading costs about 1s warm and the first ever call downloads roughly 90 MB,
    so it is never loaded until a query asks to rerank. Left on the default ONNX
    thread pool, which is the fast setting here: capping it made a 20-candidate
    rerank 106ms to 256ms. The pool spins for about two seconds afterwards, which
    is tolerable for an opt-in call and is why the daemon's keepalive does not
    touch this model.
    """
    with _LOAD_LOCK:
        if "model" not in _RERANK_CACHE:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            _RERANK_CACHE["model"] = TextCrossEncoder(model_name=RERANK_MODEL,
                                                      providers=QUERY_PROVIDERS)
    return _RERANK_CACHE["model"]


def rerank_results(query: str, results: list[dict], cursor: sqlite3.Cursor) -> list[dict]:
    """Reorder fused results by reading each section against the query.

    Fusion ranks a section by how two independent lists ranked it. A cross-encoder
    reads the pair, so it can tell a section that answers the question from one
    that shares its vocabulary. Sections without indexed text fall back to their
    heading, which is what a vector-only hit for an image or an empty section has.
    """
    section_ids = [result["section_id"] for result in results]
    placeholders = ",".join("?" * len(section_ids))
    texts = dict(cursor.execute(
        f"SELECT section_id, content FROM sections_fts WHERE section_id IN ({placeholders})",
        section_ids,
    ).fetchall())
    documents = [texts.get(result["section_id"]) or result["heading"] or "" for result in results]
    for result, score in zip(results, get_cross_encoder().rerank(query, documents)):
        result["rerank_score"] = float(score)
    return sorted(results, key=lambda result: -result["rerank_score"])


@dataclass(frozen=True)
class Section:
    section_id: str
    path: str
    heading: str
    start_line: int
    chunk_index: int
    sha256: str
    text: str


@dataclass(frozen=True)
class Link:
    source_path: str
    raw_target: str
    resolved_target_path: str | None
    start_line: int


def default_db_path(root: Path) -> Path:
    """Keep the index out of sight in a vault, beside the corpus anywhere else.

    A transcript root has no `.obsidian` to hide in, so it gets a dotfile rather
    than a directory nobody else would look in.
    """
    return root / ".obsidian" / "pkm_index.db" if (root / ".obsidian").is_dir() else root / ".pkm_index.db"


def find_vault_root() -> Path:
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / ".obsidian").exists() or (parent / ".git").exists():
            return parent
    return current


def get_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def parse_frontmatter(content: str) -> tuple[dict, str, int]:
    """Return selected metadata, body text, and the body's absolute first line."""
    meta = {"energy": None, "sentiment": None, "sentiment_label": [], "tags": []}
    match = FRONTMATTER_RE.match(content)
    if not match:
        return meta, content, 1

    frontmatter = match.group(1)
    body = content[match.end() :]
    body_start_line = content[: match.end()].count("\n") + 1

    energy_match = re.search(r"^energy:\s*(\d+)", frontmatter, re.MULTILINE)
    if energy_match:
        meta["energy"] = int(energy_match.group(1))

    sentiment_match = re.search(
        r"^sentiment:\s*\n((?:\s*-\s*\d+\s*\n?)+)", frontmatter, re.MULTILINE
    )
    if sentiment_match:
        scores = [int(score) for score in re.findall(r"\d+", sentiment_match.group(1))]
        if scores:
            meta["sentiment"] = sum(scores) / len(scores)

    label_match = re.search(
        r"^sentiment-label:\s*\n((?:\s*-\s*[^\n]+\s*\n?)+)", frontmatter, re.MULTILINE
    )
    if label_match:
        meta["sentiment_label"] = [
            label.strip("- ").strip() for label in label_match.group(1).strip().splitlines()
        ]

    tag_match = re.search(r"^tags:\s*\n((?:\s*-\s*[^\n]+\s*\n?)+)", frontmatter, re.MULTILINE)
    if tag_match:
        meta["tags"] = [tag.strip("- ").strip() for tag in tag_match.group(1).strip().splitlines()]

    return meta, body, body_start_line


def extract_key_lines(body: str, max_lines: int = 15) -> str:
    extracted = []
    for line in body.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        if line_clean.startswith("#") or line_clean.startswith("- [ ]") or line_clean.startswith("- [x]") or line_clean.startswith("- "):
            if len(line_clean) > 200:
                line_clean = line_clean[:200] + "..."
            extracted.append(line_clean)
            if len(extracted) >= max_lines:
                break
    return "\n".join(extracted)


def iter_wikilinks(content: str):
    """Yield raw wikilinks and their absolute source lines."""
    for match in WIKILINK_RE.finditer(content):
        raw_target = match.group(1).strip()
        if not raw_target:
            continue
        start_line = content.count("\n", 0, match.start()) + 1
        yield raw_target, start_line


def clean_link_target(raw_target: str) -> str:
    return raw_target.split("|", 1)[0].split("#", 1)[0].strip().replace("\\", "/")


def normalise_note_key(value: str) -> str:
    clean = value.strip().replace("\\", "/")
    if clean.lower().endswith(".md"):
        clean = clean[:-3]
    return clean.lstrip("/").casefold()


def make_note_lookup(paths: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    by_path = {}
    by_stem = defaultdict(list)
    for path in paths:
        by_path[normalise_note_key(path)] = path
        by_stem[Path(path).stem.casefold()].append(path)
    return by_path, by_stem


def resolve_wikilink(
    raw_target: str, source_path: str, by_path: dict[str, str], by_stem: dict[str, list[str]]
) -> str | None:
    target = clean_link_target(raw_target)
    if not target:
        return None

    direct = by_path.get(normalise_note_key(target))
    if direct:
        return direct

    if "/" in target:
        source_dir = PurePosixPath(source_path).parent
        relative_target = str(source_dir / target)
        resolved = by_path.get(normalise_note_key(relative_target))
        if resolved:
            return resolved

    candidates = by_stem.get(Path(target).name.casefold(), [])
    return candidates[0] if len(candidates) == 1 else None


def parse_sections(file_stem: str, body: str, body_start_line: int) -> list[tuple[str, int, str]]:
    """Split on H2 headings while keeping absolute source locations."""
    lines = body.splitlines()
    heading_positions = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not heading_positions:
        text = body.strip()
        return [(file_stem, body_start_line, text)] if text else []

    sections = []
    preamble = "\n".join(lines[: heading_positions[0]]).strip()
    if preamble:
        sections.append((file_stem, body_start_line, preamble))

    for position_index, heading_position in enumerate(heading_positions):
        next_position = (
            heading_positions[position_index + 1]
            if position_index + 1 < len(heading_positions)
            else len(lines)
        )
        heading = lines[heading_position][3:].strip() or file_stem
        text = "\n".join(lines[heading_position + 1 : next_position]).strip() or heading
        sections.append((heading, body_start_line + heading_position, text))

    return sections


def estimate_tokens(text: str) -> int:
    """Use a conservative local estimate when the model tokenizer is unavailable."""
    estimate = 0
    for token in TOKEN_RE.findall(text):
        if token.isalnum() or token == "_":
            estimate += max(1, (len(token) + 3) // 4)
        else:
            estimate += 1
    return estimate


def chunk_section(heading: str, text: str) -> list[str]:
    """Return heading-aware chunks within a conservative embedding budget."""
    clean_text = " ".join(text.split())
    prefix = heading.strip() or "Untitled"
    if estimate_tokens(prefix + " " + clean_text) <= MAX_CHUNK_ESTIMATED_TOKENS:
        return [f"{prefix}\n{clean_text}"]

    words = clean_text.split()
    chunks = []
    start = 0
    prefix_cost = estimate_tokens(prefix) + 1

    while start < len(words):
        end = start
        budget = prefix_cost
        while end < len(words):
            word_cost = estimate_tokens(words[end]) + 1
            if end > start and budget + word_cost > MAX_CHUNK_ESTIMATED_TOKENS:
                break
            budget += word_cost
            end += 1

        chunks.append(f"{prefix}\n{' '.join(words[start:end])}")
        if end >= len(words):
            break

        next_start = end
        overlap_cost = 0
        while next_start > start + 1:
            previous_cost = estimate_tokens(words[next_start - 1]) + 1
            if overlap_cost + previous_cost > CHUNK_OVERLAP_ESTIMATED_TOKENS:
                break
            overlap_cost += previous_cost
            next_start -= 1
        start = next_start

    return chunks


def category_for(path: str) -> str:
    filename = PurePosixPath(path).name
    if filename.startswith("day "):
        return "daily"
    if filename.startswith("review "):
        return "review"
    if path.startswith("work/"):
        parts = path.split("/")
        return f"work/{parts[1]}" if len(parts) > 2 else "work"
    return "general"


def markdown_paths(vault_dir: Path) -> list[Path]:
    """Every markdown file in the vault, skipping any repository nested inside it.

    A vault that mounts another vault, as a clone or a junction, is two corpora
    sharing a folder rather than one large one. Indexing them together lets the
    larger one swamp the smaller in every ranking, so a directory holding its own
    `.git` is left for its own index.
    """
    paths = []
    for root, directories, files in os.walk(vault_dir):
        directories[:] = [directory for directory in directories
                          if directory not in IGNORED_DIRS
                          and not (Path(root) / directory / ".git").exists()]
        for filename in files:
            if filename.endswith(".md"):
                paths.append(Path(root) / filename)
    return sorted(paths)


def last_index_run(db_path) -> str | None:
    """When the index last finished, as the ISO string the run was written with."""
    if not Path(db_path).exists():
        return None
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return connection.execute("SELECT MAX(completed_at) FROM index_runs").fetchone()[0]
    except sqlite3.DatabaseError:  # no index_runs table yet, or not a database
        return None
    finally:
        connection.close()


def stale_paths(vault_dir, db_path, limit: int = 25) -> dict:
    """Files on disk the index has not read yet, so a search can say what it missed.

    A search that ranks well over a stale index is indistinguishable from one
    that works. On 2026-08-28 that cost three days: the brain index last ran on
    the 25th and every note written since matched zero rows, with nothing in the
    output to say so.

    mtime against the last run rather than a content hash, because reading three
    thousand files to answer a twenty millisecond query defeats the point. A
    touched-but-unchanged file costs one reindex that finds nothing to do, and a
    file written during a run is caught by the next one. Walking 3,272 files and
    stat-ing each takes 0.09s.
    """
    completed_at = last_index_run(db_path)
    if completed_at is None:
        return {"count": 0, "paths": [], "indexed_at": None, "no_index": True}
    root = Path(vault_dir)
    cutoff = datetime.fromisoformat(completed_at).timestamp()
    newer = []
    for path in markdown_paths(root):
        try:
            if path.stat().st_mtime > cutoff:
                newer.append(path.relative_to(root).as_posix())
        except OSError:  # deleted between the walk and the stat
            continue
    return {"count": len(newer), "paths": newer[:limit], "indexed_at": completed_at}


def collect_index_data(vault_dir: Path):
    file_paths = markdown_paths(vault_dir)
    relative_paths = [path.relative_to(vault_dir).as_posix() for path in file_paths]
    by_path, by_stem = make_note_lookup(relative_paths)

    notes = []
    sections = []
    links = []
    errors = []

    for full_path, relative_path in zip(file_paths, relative_paths):
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            meta, body, body_start_line = parse_frontmatter(content)
            notes.append(
                (
                    relative_path,
                    full_path.name,
                    category_for(relative_path),
                    meta["energy"],
                    meta["sentiment"],
                    json.dumps(meta["sentiment_label"]),
                    json.dumps(meta["tags"]),
                    extract_key_lines(body),
                    len(body.split()),
                )
            )

            for raw_target, start_line in iter_wikilinks(content):
                links.append(
                    Link(
                        source_path=relative_path,
                        raw_target=raw_target,
                        resolved_target_path=resolve_wikilink(raw_target, relative_path, by_path, by_stem),
                        start_line=start_line,
                    )
                )

            for section_ordinal, (heading, start_line, section_text) in enumerate(
                parse_sections(full_path.stem, body, body_start_line)
            ):
                for chunk_index, chunk_text in enumerate(chunk_section(heading, section_text)):
                    section_id = f"{relative_path}::{section_ordinal}:{chunk_index}"
                    sections.append(
                        Section(
                            section_id=section_id,
                            path=relative_path,
                            heading=heading,
                            start_line=start_line,
                            chunk_index=chunk_index,
                            sha256=get_sha256(chunk_text),
                            text=chunk_text,
                        )
                    )
        except Exception as error:
            errors.append((relative_path, "parse", str(error)))

    return notes, sections, links, errors


def table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def ensure_schema(connection: sqlite3.Connection):
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA busy_timeout=60000;")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            path TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            category TEXT NOT NULL,
            energy INTEGER,
            sentiment REAL,
            sentiment_labels TEXT NOT NULL,
            tags TEXT NOT NULL,
            summary_snippet TEXT NOT NULL,
            word_count INTEGER NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sections (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            heading TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            sha256 TEXT NOT NULL,
            embedding_model TEXT,
            chunking_version TEXT,
            vector BLOB
        )
        """
    )
    section_columns = table_columns(connection, "sections")
    for column, definition in (
        ("chunk_index", "INTEGER NOT NULL DEFAULT 0"),
        ("embedding_model", "TEXT"),
        ("chunking_version", "TEXT"),
    ):
        if column not in section_columns:
            connection.execute(f"ALTER TABLE sections ADD COLUMN {column} {definition}")

    connection.execute("CREATE INDEX IF NOT EXISTS idx_sections_path ON sections(path)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_sections_sha ON sections(sha256)")

    edge_columns = table_columns(connection, "edges")
    required_edge_columns = {"source_path", "raw_target", "resolved_target_path", "start_line"}
    if edge_columns and not required_edge_columns.issubset(edge_columns):
        connection.execute("DROP TABLE edges")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS edges (
            source_path TEXT NOT NULL,
            raw_target TEXT NOT NULL,
            resolved_target_path TEXT,
            start_line INTEGER NOT NULL,
            PRIMARY KEY (source_path, raw_target, start_line)
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_path)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_edges_resolved_target ON edges(resolved_target_path)")

    fts_columns = table_columns(connection, "sections_fts")
    if fts_columns and fts_columns != {"section_id", "content"}:
        connection.execute("DROP TABLE sections_fts")
    title_fts_columns = table_columns(connection, "note_titles_fts")
    if title_fts_columns and title_fts_columns != {"path", "title"}:
        connection.execute("DROP TABLE note_titles_fts")

    try:
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
                section_id UNINDEXED,
                content,
                tokenize='unicode61'
            )
            """
        )
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS note_titles_fts USING fts5(
                path UNINDEXED,
                title,
                tokenize='unicode61'
            )
            """
        )
    except sqlite3.OperationalError as error:
        raise RuntimeError("This SQLite build needs FTS5 support.") from error

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS index_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            vault_path TEXT NOT NULL,
            status TEXT NOT NULL,
            note_count INTEGER NOT NULL,
            section_count INTEGER NOT NULL,
            embedding_count INTEGER NOT NULL,
            error_count INTEGER NOT NULL
        )
        """
    )
    run_columns = table_columns(connection, "index_runs")
    for column, definition in (
        ("duration_seconds", "REAL"),
        ("scan_seconds", "REAL"),
        ("embed_seconds", "REAL"),
        ("db_seconds", "REAL"),
        ("provider", "TEXT"),
    ):
        if column not in run_columns:
            connection.execute(f"ALTER TABLE index_runs ADD COLUMN {column} {definition}")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS index_errors (
            run_id INTEGER NOT NULL,
            path TEXT NOT NULL,
            stage TEXT NOT NULL,
            message TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES index_runs(id)
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_index_errors_run ON index_errors(run_id)")
    connection.execute("CREATE TABLE IF NOT EXISTS index_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute(
        "INSERT INTO index_meta(key, value) VALUES ('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (SCHEMA_VERSION,),
    )


def load_vector_cache(connection: sqlite3.Connection):
    by_id = {}
    by_hash = {}
    rows = connection.execute(
        "SELECT id, sha256, embedding_model, chunking_version, vector FROM sections"
    ).fetchall()
    for section_id, sha256, model, chunking_version, vector in rows:
        vector_bytes = bytes(vector) if vector is not None else None
        value = (sha256, model, chunking_version, vector_bytes)
        by_id[section_id] = value
        if vector_bytes is not None:
            by_hash[(sha256, model, chunking_version)] = vector_bytes
    return by_id, by_hash


def create_embeddings(
    sections: list[Section], connection: sqlite3.Connection | None = None
) -> tuple[dict[str, bytes], str]:
    if not sections:
        return {}, "None"
    if not HAS_FASTEMBED:
        raise RuntimeError("fastembed is required for embeddings. Use --skip-embeddings for metadata-only indexing.")

    providers = get_embedding_providers()
    active_provider = providers[0] if providers else "CPUExecutionProvider"
    model = get_embedding_model(providers)
    vectors = {}
    batch_size = 32
    for batch_start in range(0, len(sections), batch_size):
        batch = sections[batch_start : batch_start + batch_size]
        batch_rows = []
        try:
            raw_vectors = list(model.embed([section.text for section in batch], batch_size=batch_size))
        except Exception:
            active_provider = "CPUExecutionProvider (Fallback)"
            fallback_model = get_embedding_model(["CPUExecutionProvider"])
            raw_vectors = list(fallback_model.embed([section.text for section in batch], batch_size=16))

        for section, vector in zip(batch, raw_vectors):
            vector_array = np.asarray(vector, dtype=np.float32)
            if vector_array.size != EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    f"Expected {EMBEDDING_DIMENSIONS} dimensions from {EMBEDDING_MODEL}, got {vector_array.size}."
                )
            norm = np.linalg.norm(vector_array)
            if norm > 0:
                vector_array = vector_array / norm
            vec_bytes = vector_array.tobytes()
            vectors[section.section_id] = vec_bytes
            batch_rows.append((
                section.section_id,
                section.path,
                section.heading,
                section.start_line,
                section.chunk_index,
                section.sha256,
                EMBEDDING_MODEL,
                CHUNKING_VERSION,
                vec_bytes,
            ))
        
        # Per-batch checkpoint to SQLite so progress is never lost on interruption/timeout
        if connection is not None and batch_rows:
            with connection:
                connection.executemany(
                    """
                    INSERT INTO sections
                    (id, path, heading, start_line, chunk_index, sha256, embedding_model, chunking_version, vector)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        path = excluded.path,
                        heading = excluded.heading,
                        start_line = excluded.start_line,
                        chunk_index = excluded.chunk_index,
                        sha256 = excluded.sha256,
                        embedding_model = excluded.embedding_model,
                        chunking_version = excluded.chunking_version,
                        vector = excluded.vector
                    """,
                    batch_rows,
                )

        completed = min(batch_start + batch_size, len(sections))
        if completed % 512 == 0 or completed == len(sections):
            print(f"Embedded {completed:,}/{len(sections):,} sections.", flush=True)
    return vectors, active_provider


def remove_missing_rows(cursor: sqlite3.Cursor, table: str, key_column: str, seen_values: set[str]) -> int:
    existing_values = {row[0] for row in cursor.execute(f"SELECT {key_column} FROM {table}")}
    stale_values = existing_values - seen_values
    if stale_values:
        cursor.executemany(
            f"DELETE FROM {table} WHERE {key_column} = ?", ((value,) for value in stale_values)
        )
    return len(stale_values)


def build_index(vault_path: str | None = None, db_path: str | None = None, skip_embeddings: bool = False,
                collect=None):
    t_start = time.perf_counter()
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else default_db_path(vault_dir)
    database_file.parent.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()

    connection = sqlite3.connect(database_file, timeout=60.0)
    try:
        ensure_schema(connection)
        connection.commit()
        existing_by_id, vectors_by_hash = load_vector_cache(connection)

        t_scan_start = time.perf_counter()
        notes, sections, links, errors = (collect or collect_index_data)(vault_dir)
        scan_seconds = time.perf_counter() - t_scan_start

        t_cache_start = time.perf_counter()
        vectors_by_id = {}
        sections_to_embed = []
        unchanged_vectors = 0
        reused_vectors = 0
        for section in sections:
            existing = existing_by_id.get(section.section_id)
            if (
                existing
                and existing[:3] == (section.sha256, EMBEDDING_MODEL, CHUNKING_VERSION)
                and existing[3] is not None
            ):
                vectors_by_id[section.section_id] = existing[3]
                unchanged_vectors += 1
                continue

            cached_vector = vectors_by_hash.get((section.sha256, EMBEDDING_MODEL, CHUNKING_VERSION))
            if cached_vector is not None:
                vectors_by_id[section.section_id] = cached_vector
                reused_vectors += 1
            elif not skip_embeddings:
                sections_to_embed.append(section)
        cache_seconds = time.perf_counter() - t_cache_start

        t_embed_start = time.perf_counter()
        active_provider = "Skipped" if skip_embeddings else "None"
        if sections_to_embed and not skip_embeddings:
            generated_vectors, active_provider = create_embeddings(sections_to_embed, connection=connection)
        else:
            generated_vectors = {}
        vectors_by_id.update(generated_vectors)
        embed_seconds = time.perf_counter() - t_embed_start

        section_rows = [
            (
                section.section_id,
                section.path,
                section.heading,
                section.start_line,
                section.chunk_index,
                section.sha256,
                EMBEDDING_MODEL,
                CHUNKING_VERSION,
                vectors_by_id.get(section.section_id),
            )
            for section in sections
        ]
        completed_at = datetime.now(timezone.utc).isoformat()
        status = "metadata-only" if skip_embeddings else "complete"

        t_db_start = time.perf_counter()
        with connection:
            cursor = connection.cursor()
            cursor.executemany(
                """
                INSERT INTO notes
                (path, filename, category, energy, sentiment, sentiment_labels, tags, summary_snippet, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename = excluded.filename,
                    category = excluded.category,
                    energy = excluded.energy,
                    sentiment = excluded.sentiment,
                    sentiment_labels = excluded.sentiment_labels,
                    tags = excluded.tags,
                    summary_snippet = excluded.summary_snippet,
                    word_count = excluded.word_count
                """,
                notes,
            )
            removed_notes = remove_missing_rows(cursor, "notes", "path", {note[0] for note in notes})

            cursor.executemany(
                """
                INSERT INTO sections
                (id, path, heading, start_line, chunk_index, sha256, embedding_model, chunking_version, vector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    path = excluded.path,
                    heading = excluded.heading,
                    start_line = excluded.start_line,
                    chunk_index = excluded.chunk_index,
                    sha256 = excluded.sha256,
                    embedding_model = excluded.embedding_model,
                    chunking_version = excluded.chunking_version,
                    vector = excluded.vector
                """,
                section_rows,
            )
            removed_sections = remove_missing_rows(
                cursor, "sections", "id", {section.section_id for section in sections}
            )

            cursor.execute("DELETE FROM sections_fts")
            cursor.executemany(
                "INSERT INTO sections_fts(section_id, content) VALUES (?, ?)",
                ((section.section_id, section.text) for section in sections),
            )

            cursor.execute("DELETE FROM note_titles_fts")
            cursor.executemany(
                "INSERT INTO note_titles_fts(path, title) VALUES (?, ?)",
                ((note[0], Path(note[1]).stem) for note in notes),
            )

            cursor.execute("DELETE FROM edges")
            cursor.executemany(
                """
                INSERT OR IGNORE INTO edges(source_path, raw_target, resolved_target_path, start_line)
                VALUES (?, ?, ?, ?)
                """,
                (
                    (link.source_path, link.raw_target, link.resolved_target_path, link.start_line)
                    for link in links
                ),
            )

            total_duration = time.perf_counter() - t_start
            cursor.execute(
                """
                INSERT INTO index_runs
                (started_at, completed_at, vault_path, status, note_count, section_count, embedding_count, error_count,
                 duration_seconds, scan_seconds, embed_seconds, db_seconds, provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started_at,
                    completed_at,
                    str(vault_dir),
                    status,
                    len(notes),
                    len(sections),
                    sum(vector is not None for vector in vectors_by_id.values()),
                    len(errors),
                    total_duration,
                    scan_seconds,
                    embed_seconds,
                    time.perf_counter() - t_db_start,
                    active_provider,
                ),
            )
            run_id = cursor.lastrowid
            if errors:
                cursor.executemany(
                    "INSERT INTO index_errors(run_id, path, stage, message) VALUES (?, ?, ?, ?)",
                    ((run_id, path, stage, message) for path, stage, message in errors),
                )
        db_seconds = time.perf_counter() - t_db_start
        total_duration = time.perf_counter() - t_start

        print(f"Indexed {len(notes):,} notes, {len(sections):,} sections, and {len(links):,} links.")
        print(
            f"Vectors: {unchanged_vectors:,} unchanged, {reused_vectors:,} reused by hash, "
            f"{len(generated_vectors):,} generated."
        )
        print(f"Removed {removed_notes:,} notes and {removed_sections:,} sections no longer in the vault.")
        
        # Performance timing breakdown
        notes_per_sec = len(notes) / max(scan_seconds, 0.001)
        links_per_sec = len(links) / max(scan_seconds, 0.001)
        embed_rate = len(generated_vectors) / max(embed_seconds, 0.001) if generated_vectors else 0.0
        
        print("\n--- Performance Timing ---")
        print(f"  Vault Scan & Parse:   {scan_seconds:6.2f}s  ({notes_per_sec:,.0f} notes/s, {links_per_sec:,.0f} links/s)")
        print(f"  Vector Cache & Diff:  {cache_seconds:6.2f}s  ({unchanged_vectors + reused_vectors:,} cached)")
        if generated_vectors:
            print(f"  Embedding Generation: {embed_seconds:6.2f}s  ({len(generated_vectors):,} generated, {embed_rate:.1f} vec/s [{active_provider}])")
        elif skip_embeddings:
            print(f"  Embedding Generation:  skipped (metadata-only)")
        else:
            print(f"  Embedding Generation:   0.00s (all vectors up to date)")
        print(f"  SQLite & FTS5 Commit: {db_seconds:6.2f}s  ({len(notes) + len(sections) + len(links):,} records written)")
        print(f"  Total Run Duration:   {total_duration:6.2f}s")
        print("--------------------------\n")
        
        if errors:
            print(f"Completed with {len(errors)} parse errors. See --stats for the latest run.")
        else:
            print(f"Indexing complete ({status}).")
        return {
            "notes": len(notes),
            "sections": len(sections),
            "links": len(links),
            "vectors": sum(vector is not None for vector in vectors_by_id.values()),
            "errors": len(errors),
            "run_id": run_id,
        }
    finally:
        connection.close()


# A term appearing in more than this share of sections cannot narrow anything
# down. Tuned against a 6,550 section vault, where 10% still keeps "notes".
FTS_COMMON_RATIO = 0.10


def prune_common_terms(cursor: sqlite3.Cursor, terms: list[str]) -> list[str]:
    """Drop terms too common to carry signal, keeping the rarest if all are.

    Terms are ORed, so one stopword-ish word matches thousands of rows and
    `snippet()` then runs over the best 50 of them. Measured here: "how do i
    keep the index up to date" costs 17.6ms whole and 2.4ms once "how do i the
    up to" are dropped, and ranks better for it. Frequencies come from an
    fts5vocab shadow table over the existing index, which costs 0.1-0.4ms and
    stores nothing.
    """
    try:
        cursor.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS sections_vocab USING fts5vocab('sections_fts', 'row')"
        )
        total = cursor.execute("SELECT COUNT(*) FROM sections").fetchone()[0]
        counts = {
            term: (cursor.execute("SELECT doc FROM sections_vocab WHERE term = ?", (term,)).fetchone() or [0])[0]
            for term in terms
        }
    except sqlite3.OperationalError:  # read-only database, or no index yet
        return terms
    if not total:
        return terms
    kept = [term for term in terms if 0 < counts[term] <= total * FTS_COMMON_RATIO]
    if kept:
        return kept
    known = [term for term in terms if counts[term]]
    return [min(known, key=counts.get)] if known else terms


def fts_query(query: str, cursor: sqlite3.Cursor | None = None) -> str:
    terms = re.findall(r"\w+", query.lower(), flags=re.UNICODE)
    if cursor is not None and len(terms) > 1:
        terms = prune_common_terms(cursor, terms)
    return " OR ".join(f'"{term}"' for term in terms)


def load_vectors(cursor: sqlite3.Cursor):
    """Read every stored vector into one matrix, with the row metadata beside it.

    On a 6.5k section vault this is 10 MB, 22ms of SQLite and 10ms of stacking,
    which is most of the cost of a warm query. A one-shot CLI call pays it once
    and does not care; a daemon should hand in the result instead (see
    `searchd.py`), which is why this is a separate function.
    """
    rows = cursor.execute(
        """
        SELECT id, path, heading, start_line, vector
        FROM sections
        WHERE vector IS NOT NULL AND embedding_model = ? AND chunking_version = ?
        """,
        (EMBEDDING_MODEL, CHUNKING_VERSION),
    ).fetchall()
    if not rows:
        return [], None
    meta = [(row[0], row[1], row[2], row[3]) for row in rows]
    matrix = np.vstack([np.frombuffer(row[4], dtype=np.float32) for row in rows])
    return meta, matrix


def search_index(
    query: str,
    vault_path: str | None = None,
    db_path: str | None = None,
    limit: int = 10,
    vectors: tuple | None = None,
    rerank: bool = False,
) -> list[dict]:
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else default_db_path(vault_dir)
    if not database_file.exists():
        print(f"Index database not found at {database_file}. Run indexing first.")
        return []

    connection = sqlite3.connect(database_file, timeout=60.0)
    try:
        cursor = connection.cursor()
        lexical_results = {}
        query_expression = fts_query(query, cursor)
        if query_expression:
            rows = cursor.execute(
                """
                SELECT sections.id, sections.path, sections.heading, sections.start_line,
                       snippet(sections_fts, 1, '[', ']', '...', 24)
                FROM sections_fts
                JOIN sections ON sections.id = sections_fts.section_id
                WHERE sections_fts MATCH ?
                ORDER BY bm25(sections_fts)
                LIMIT 50
                """,
                (query_expression,),
            ).fetchall()
            for rank, row in enumerate(rows, 1):
                lexical_results[row[0]] = {
                    "path": row[1],
                    "heading": row[2],
                    "start_line": row[3],
                    "lex_rank": rank,
                    "snippet": row[4],
                }

        vector_results = {}
        meta, matrix = vectors if vectors is not None else load_vectors(cursor)
        if matrix is not None:
            if not HAS_FASTEMBED:
                print("fastembed is unavailable; returning lexical results only.")
            else:
                model = get_embedding_model(QUERY_PROVIDERS, QUERY_THREADS)
                query_vector = np.asarray(next(model.embed([query])), dtype=np.float32)
                norm = np.linalg.norm(query_vector)
                if norm > 0:
                    query_vector = query_vector / norm
                scores = matrix @ query_vector
                for rank, index in enumerate(np.argsort(-scores)[:50], 1):
                    section_id, path, heading, start_line = meta[index]
                    vector_results[section_id] = {
                        "path": path,
                        "heading": heading,
                        "start_line": start_line,
                        "vec_rank": rank,
                        "raw_sim": float(scores[index]),
                    }

        results = []
        for section_id in set(lexical_results) | set(vector_results):
            lexical = lexical_results.get(section_id)
            semantic = vector_results.get(section_id)
            source = semantic or lexical
            score = 0.0
            if lexical:
                score += 1.0 / (60 + lexical["lex_rank"])
            if semantic:
                score += 1.0 / (60 + semantic["vec_rank"])
            results.append(
                {
                    "section_id": section_id,
                    "path": source["path"],
                    "heading": source["heading"],
                    "start_line": source["start_line"],
                    "score": score,
                    "lex_rank": lexical["lex_rank"] if lexical else None,
                    "vec_rank": semantic["vec_rank"] if semantic else None,
                    "raw_sim": semantic["raw_sim"] if semantic else None,
                    "snippet": lexical["snippet"] if lexical else None,
                }
            )
        ranked = sorted(results, key=lambda result: -result["score"])
        if rerank and ranked:
            if not HAS_FASTEMBED:
                print("fastembed is unavailable; returning fused results unranked.")
            else:
                ranked = rerank_results(query, ranked[:RERANK_CANDIDATES], cursor)
        return ranked[:limit]
    finally:
        connection.close()


def find_similar_notes(
    note_reference: str,
    vault_path: str | None = None,
    db_path: str | None = None,
    limit: int = 10,
    vectors: tuple | None = None,
) -> list[dict] | None:
    """Nearest notes to a note that is already indexed, without encoding a query.

    `search_index` spends ~220ms encoding its query string on the CPU provider,
    which dwarfs the comparison itself. A note in the index already has vectors:
    pool its own sections into one vector and compare that against the matrix.
    Returns None when the reference does not resolve to exactly one note, so the
    caller can tell "unknown note" apart from "no neighbours".
    """
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else default_db_path(vault_dir)
    if not database_file.exists():
        return None

    connection = sqlite3.connect(f"file:{database_file}?mode=ro", uri=True, timeout=60.0)
    try:
        cursor = connection.cursor()
        matches = find_note_paths(cursor, note_reference)
        if len(matches) != 1:
            return None
        path = matches[0]
        meta, matrix = vectors if vectors is not None else load_vectors(cursor)
        if matrix is None:
            return []
        own = [index for index, row in enumerate(meta) if row[1] == path]
        if not own:
            return []
        query_vector = matrix[own].mean(axis=0)
        norm = np.linalg.norm(query_vector)
        if norm == 0:
            return []
        scores = matrix @ (query_vector / norm)

        results = []
        seen = {path}  # a note is never its own neighbour
        for rank, index in enumerate(np.argsort(-scores), 1):
            _, row_path, heading, start_line = meta[index]
            if row_path in seen:
                continue
            seen.add(row_path)  # one row per note, its best-matching section
            results.append(
                {
                    "path": row_path,
                    "heading": heading,
                    "start_line": start_line,
                    "score": float(scores[index]),
                    "lex_rank": None,
                    "vec_rank": rank,
                    "raw_sim": float(scores[index]),
                    "snippet": None,
                }
            )
            if len(results) >= limit:
                break
        return results
    finally:
        connection.close()


def title_matches(cursor: sqlite3.Cursor, title: str, limit: int = 5) -> list[str]:
    expression = fts_query(title)
    if not expression:
        return []
    rows = cursor.execute(
        """
        SELECT path
        FROM note_titles_fts
        WHERE note_titles_fts MATCH ?
        ORDER BY bm25(note_titles_fts)
        LIMIT ?
        """,
        (expression, limit),
    ).fetchall()
    return [row[0] for row in rows]


# The cosine at which two notes are treated as the same note. Measured over 80
# vault notes by re-querying each note's own title: it scores >= 0.85 against
# its own sections for 59% of them, while the best *unrelated* note clears 0.85
# for 4%. Lower catches more rewrites (0.80: 80% caught) but blocks far more
# good notes (35% false), and a gate whose block is usually wrong gets disabled.
DUPLICATE_THRESHOLD = 0.85


def duplicate_matches(
    inputs: list[str],
    vault_path: str | None = None,
    db_path: str | None = None,
    limit: int = 5,
    vectors: tuple | None = None,
) -> dict[str, list[dict]] | None:
    """Best cosine per note for each input title or note path. None = cannot check.

    Ranked on raw cosine alone. `title_rank` is carried for display only: title
    FTS fires on common words, so ranking on it puts five same-word notes above
    the note that is actually the same note, and a threshold read off that order
    is meaningless. It also scores the whole matrix rather than `search_index`'s
    top-50 cut, so a candidate cannot fall off the end before it is compared.

    Every input is embedded in one batch, so a caller with ten new notes pays
    the ~2s model load once. An input ending in `.md` is a path: its title is
    the filename stem and a note with that same stem is skipped, because a note
    already in the index is not its own duplicate.
    """
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else default_db_path(vault_dir)
    if not database_file.exists() or not HAS_FASTEMBED:
        return None

    connection = sqlite3.connect(database_file, timeout=60.0)
    try:
        cursor = connection.cursor()
        meta, matrix = vectors if vectors is not None else load_vectors(cursor)
        if matrix is None:
            return None

        titles = [Path(value).stem if value.casefold().endswith(".md") else value for value in inputs]
        model = get_embedding_model(QUERY_PROVIDERS, QUERY_THREADS)
        queries = np.asarray(list(model.embed(titles)), dtype=np.float32)
        queries /= np.maximum(np.linalg.norm(queries, axis=1, keepdims=True), 1e-12)
        scores = matrix @ queries.T  # sections x inputs

        found = {}
        for column, (value, title) in enumerate(zip(inputs, titles)):
            ranks = {path: rank for rank, path in enumerate(title_matches(cursor, title), 1)}
            skip_stem = title if value.casefold().endswith(".md") else None
            best: dict[str, dict] = {}
            for row, (_, path, heading, start_line) in enumerate(meta):
                if Path(path).stem == skip_stem:
                    continue
                cosine = float(scores[row, column])
                if path not in best or cosine > best[path]["cosine"]:
                    best[path] = {
                        "path": path,
                        "cosine": cosine,
                        "heading": heading,
                        "start_line": start_line,
                        "title_rank": ranks.get(path),
                    }
            found[value] = sorted(best.values(), key=lambda match: -match["cosine"])[:limit]
        return found
    finally:
        connection.close()


def check_duplicate(
    title: str,
    vault_path: str | None = None,
    db_path: str | None = None,
    threshold: float = DUPLICATE_THRESHOLD,
    as_json: bool = False,
    vectors: tuple | None = None,
) -> int:
    return check_duplicate_batch([title], vault_path, db_path, threshold, as_json, vectors)


def check_duplicate_batch(
    inputs: list[str],
    vault_path: str | None = None,
    db_path: str | None = None,
    threshold: float = DUPLICATE_THRESHOLD,
    as_json: bool = False,
    vectors: tuple | None = None,
) -> int:
    """Report likely existing notes and return a process exit code.

    0 clean, 1 at least one match at or above `threshold`, 2 the check could not
    run because the index is missing or holds no vectors. A gate has to tell a
    duplicate from a broken check: one asks the writer to merge, the other asks
    the owner to reindex, and a hook that confuses them blocks every commit.
    """
    found = duplicate_matches(inputs, vault_path=vault_path, db_path=db_path, vectors=vectors)
    if found is None:
        print("Index database not found or holds no vectors. Run indexing first.", file=sys.stderr)
        if as_json:
            print(json.dumps({"threshold": threshold, "error": "index unavailable", "results": []}, indent=2))
        return 2

    results = [
        {
            "input": value,
            "duplicate": bool(matches) and matches[0]["cosine"] >= threshold,
            "matches": matches,
        }
        for value, matches in found.items()
    ]
    if as_json:
        print(json.dumps({"threshold": threshold, "results": results}, indent=2))
    else:
        for result in results:
            print(f"\nPossible existing notes for: {result['input']!r}")
            if not result["matches"]:
                print("No semantic candidates found.")
                continue
            for index, match in enumerate(result["matches"], 1):
                parts = [f"cosine {match['cosine']:.3f}"]
                if match["title_rank"] is not None:
                    parts.append(f"title rank {match['title_rank']}")
                print(f"  {index}. {match['path']} ({', '.join(parts)})")
            if result["duplicate"]:
                print(f"  at or above the {threshold} duplicate threshold")
        print("Review the candidates before deciding to append, link, merge, or create a distinct note.")
    return 1 if any(result["duplicate"] for result in results) else 0


def find_note_paths(cursor: sqlite3.Cursor, note_reference: str) -> list[str]:
    clean_reference = normalise_note_key(note_reference)
    paths = [row[0] for row in cursor.execute("SELECT path FROM notes")]
    exact = [path for path in paths if normalise_note_key(path) == clean_reference]
    if exact:
        return exact
    return [path for path in paths if Path(path).stem.casefold() == Path(clean_reference).name.casefold()]


def query_links(note_reference: str, vault_path: str | None = None, db_path: str | None = None):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else default_db_path(vault_dir)
    if not database_file.exists():
        print("Index database not found. Run indexing first.")
        return None

    connection = sqlite3.connect(database_file)
    try:
        cursor = connection.cursor()
        matches = find_note_paths(cursor, note_reference)
        if not matches:
            print(f"No indexed note matches {note_reference!r}.")
            return None
        if len(matches) > 1:
            print(f"Ambiguous note reference {note_reference!r}:")
            for path in matches[:20]:
                print(f"  {path}")
            return None

        path = matches[0]
        outbound = cursor.execute(
            """
            SELECT raw_target, resolved_target_path, start_line
            FROM edges WHERE source_path = ? ORDER BY start_line, raw_target
            """,
            (path,),
        ).fetchall()
        inbound = cursor.execute(
            """
            SELECT source_path, raw_target, start_line
            FROM edges WHERE resolved_target_path = ? ORDER BY source_path, start_line
            """,
            (path,),
        ).fetchall()
        print(f"\nLinks for: {path}")
        print(f"Outbound ({len(outbound)}):")
        for raw_target, resolved_path, start_line in outbound[:20]:
            target = resolved_path or raw_target
            print(f"  -> {target} ({path}:{start_line})")
        if len(outbound) > 20:
            print(f"  ... (+{len(outbound) - 20} more)")
        print(f"Inbound ({len(inbound)}):")
        for source_path, raw_target, start_line in inbound[:20]:
            print(f"  <- {source_path}:{start_line} via [[{raw_target}]]")
        if len(inbound) > 20:
            print(f"  ... (+{len(inbound) - 20} more)")
        return {"path": path, "outbound": outbound, "inbound": inbound}
    finally:
        connection.close()


# Unlinked mentions. Every candidate section costs one file read, so the FTS
# candidate set is capped well above anything a pane shows.
UNLINKED_CANDIDATES = 200
SNIPPET_CHARS = 120
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")


def parse_aliases(content: str) -> list[str]:
    """Return frontmatter `aliases`, in block, inline-list, or scalar form.

    The index does not store aliases, so a query reads the one target note from
    disk. That is a single file read against an FTS5 query over 6,550 sections,
    which does not show up in the timing; storing them would cost a schema
    change and a reindex to save nothing measurable.
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return []
    found = re.search(
        r"^aliases:[ \t]*([^\n]*)\n((?:[ \t]*-[ \t]*[^\n]+\n?)*)",
        match.group(1) + "\n",
        re.MULTILINE,
    )
    if not found:
        return []
    inline = found.group(1).strip().strip("[]")
    raw = (
        inline.split(",")
        if inline
        else [re.sub(r"^-\s*", "", line.strip()) for line in found.group(2).splitlines()]
    )
    return [value.strip().strip("'\"") for value in raw if value.strip()]


def fenced_lines(lines: list[str]) -> set[int]:
    """Absolute line numbers inside a ``` fence, the toggle `urgent_tasks.py` uses."""
    inside = False
    marked = set()
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            inside = not inside
            marked.add(number)
        elif inside:
            marked.add(number)
    return marked


def mark_snippet(line: str, span: tuple[int, int]) -> str:
    """Trim a line around the match and bracket it, the way `snippet()` does."""
    start, end = span
    head = line[max(0, start - SNIPPET_CHARS // 2) : start]
    tail = line[end : end + SNIPPET_CHARS // 2]
    lead = "..." if start > len(head) else ""
    trail = "..." if end + len(tail) < len(line) else ""
    return f"{lead}{head.lstrip()}[{line[start:end]}]{tail.rstrip()}{trail}"


def find_unlinked_mentions(
    note_reference: str,
    vault_path: str | None = None,
    db_path: str | None = None,
    limit: int = 20,
) -> list[dict] | None:
    """Sections naming a note without linking to it.

    Obsidian's own pane rescans the cached text of every note for the title and
    each alias whenever a note is opened, so its cost is the whole vault. This
    asks FTS5 for the candidate sections first and reads only the files behind
    them. Matching is an FTS5 phrase, so it is token-based: "covariance" does
    not match "covariances", which is the behaviour the pane's substring match
    gets wrong. Returns None when the reference names no single note.
    """
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else default_db_path(vault_dir)
    if not database_file.exists():
        print("Index database not found. Run indexing first.")
        return None

    connection = sqlite3.connect(database_file)
    try:
        cursor = connection.cursor()
        matches = find_note_paths(cursor, note_reference)
        if len(matches) != 1:
            print(f"No single indexed note matches {note_reference!r}.")
            return None

        target = matches[0]
        target_file = vault_dir / target
        names = [Path(target).stem]
        if target_file.exists():
            names += parse_aliases(target_file.read_text(encoding="utf-8", errors="ignore"))
        # Longest first, so an alias containing the title wins the alternation.
        names = sorted({name.strip() for name in names if re.search(r"\w", name)}, key=len, reverse=True)
        if not names:
            return []

        expression = " OR ".join('"{}"'.format(name.replace('"', '""')) for name in names)
        rows = cursor.execute(
            """
            SELECT sections.path, sections.heading, sections.start_line, bm25(sections_fts)
            FROM sections_fts
            JOIN sections ON sections.id = sections_fts.section_id
            WHERE sections_fts MATCH ? AND sections.path <> ?
            ORDER BY bm25(sections_fts)
            LIMIT ?
            """,
            (expression, target, UNLINKED_CANDIDATES),
        ).fetchall()

        pattern = re.compile(
            r"(?<!\w)(" + "|".join(re.escape(name) for name in names) + r")(?!\w)", re.IGNORECASE
        )
        keys = {name.casefold() for name in names}
        files: dict[str, tuple[list[str], set[int]]] = {}
        seen = set()
        hits = []
        for path, heading, start_line, score in rows:
            if len(hits) >= limit:
                break
            if (path, start_line) in seen:  # one section can be several chunks
                continue
            seen.add((path, start_line))

            if path not in files:
                note_file = vault_dir / path
                lines = (
                    note_file.read_text(encoding="utf-8", errors="ignore").splitlines()
                    if note_file.exists()
                    else []
                )
                files[path] = (lines, fenced_lines(lines))
            lines, fenced = files[path]

            following = cursor.execute(
                "SELECT MIN(start_line) FROM sections WHERE path = ? AND start_line > ?",
                (path, start_line),
            ).fetchone()[0]
            body = lines[start_line - 1 : (following or len(lines) + 1) - 1]

            # A section that already links the target is a linked mention.
            if any(
                Path(clean_link_target(raw)).name.casefold() in keys
                for raw, _ in iter_wikilinks("\n".join(body))
            ):
                continue

            for offset, line in enumerate(body):
                number = start_line + offset
                if number in fenced:
                    continue
                # Two more places a mention cannot become a link: inside a
                # `code span`, for the same reason a fence is skipped, and
                # inside a [[link]] to some other note, because
                # `[[Obsidian faster startup]]` is not a mention of `Obsidian`
                # anyone can act on.
                spans = [
                    span.span()
                    for span in list(WIKILINK_RE.finditer(line)) + list(INLINE_CODE_RE.finditer(line))
                ]
                found = next(
                    (
                        match
                        for match in pattern.finditer(line)
                        if not any(begin <= match.start() and match.end() <= close for begin, close in spans)
                    ),
                    None,
                )
                if not found:
                    continue
                hits.append(
                    {
                        "path": path,
                        "heading": heading,
                        "start_line": number,
                        "score": score,
                        "term": found.group(0),
                        "snippet": mark_snippet(line, found.span()),
                    }
                )
                break
        return hits
    finally:
        connection.close()


def print_stats(vault_path: str | None = None, db_path: str | None = None):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else default_db_path(vault_dir)
    if not database_file.exists():
        print("Database not found.")
        return

    connection = sqlite3.connect(database_file)
    try:
        ensure_schema(connection)
        cursor = connection.cursor()
        note_count = cursor.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        section_count, vector_count = cursor.execute("SELECT COUNT(*), COUNT(vector) FROM sections").fetchone()
        edge_count = cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        fts_count = cursor.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0]
        title_count = cursor.execute("SELECT COUNT(*) FROM note_titles_fts").fetchone()[0]
        runs = cursor.execute(
            """
            SELECT id, status, completed_at, note_count, section_count, embedding_count,
                   duration_seconds, scan_seconds, embed_seconds, db_seconds, provider
            FROM index_runs ORDER BY id DESC LIMIT 5
            """
        ).fetchall()

        print("\n--- PKM Index Stats ---")
        print(f"Database location: {database_file}")
        print(f"Database size:     {database_file.stat().st_size / (1024 * 1024):.2f} MB")
        print(f"Indexed notes:     {note_count:,}")
        print(f"Sections:          {section_count:,}")
        print(f"FTS sections:      {fts_count:,}")
        print(f"Title index rows:  {title_count:,}")
        print(f"Vector embeddings: {vector_count:,} ({EMBEDDING_MODEL})")
        print(f"Link graph edges:  {edge_count:,}")
        print(f"Hardware provider: {get_embedding_providers()[0] if HAS_FASTEMBED else 'fastembed unavailable'}")
        
        if runs:
            print("\n--- Recent Indexing Runs & Performance History ---")
            print(f"{'Run ID':<7} | {'Status':<13} | {'Completed At':<20} | {'Duration':<9} | {'Scan/Parse':<10} | {'Embed Time':<10} | {'DB Commit':<10}")
            print("-" * 92)
            for run in runs:
                run_id, status, completed_at, n_cnt, s_cnt, e_cnt, dur, scan_t, emb_t, db_t, prov = run
                dur_str = f"{dur:.2f}s" if dur is not None else "N/A"
                scan_str = f"{scan_t:.2f}s" if scan_t is not None else "N/A"
                emb_str = f"{emb_t:.2f}s" if emb_t is not None else "N/A"
                db_str = f"{db_t:.2f}s" if db_t is not None else "N/A"
                ts = completed_at[:19].replace("T", " ") if completed_at else "N/A"
                print(f"{run_id:<7} | {status:<13} | {ts:<20} | {dur_str:<9} | {scan_str:<10} | {emb_str:<10} | {db_str:<10}")
        print("--------------------------------------------------\n")
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description="Index Markdown metadata, sections, links, and local hybrid search.")
    parser.add_argument("--vault", type=str, default=None, help="Path to the vault root")
    parser.add_argument("--db", type=str, default=None, help="Path to the SQLite database")
    parser.add_argument(
        "--skip-embeddings", action="store_true", help="Build metadata, FTS, and links without generating vectors"
    )
    parser.add_argument("--search", type=str, default=None, help="Run hybrid search across indexed sections")
    parser.add_argument("--check-duplicate", type=str, default=None, help="Show likely existing notes before creation")
    parser.add_argument(
        "--check-duplicate-batch", nargs="+", metavar="NOTE", default=None,
        help="Check several titles or note paths in one process, paying the model load once",
    )
    parser.add_argument(
        "--threshold", type=float, default=DUPLICATE_THRESHOLD,
        help=f"Cosine at or above which a duplicate check exits 1 (default {DUPLICATE_THRESHOLD})",
    )
    parser.add_argument("--json", action="store_true", help="Emit the duplicate check as JSON on stdout")
    parser.add_argument("--links", type=str, default=None, help="Show inbound and outbound links for a note")
    parser.add_argument("--stats", "--perf", action="store_true", help="Display database and indexing performance benchmarks")
    parser.add_argument("--limit", type=int, default=10, help="Maximum search results")
    parser.add_argument("--rerank", action="store_true",
                        help="Reorder the fused top with a cross-encoder, about 533ms over "
                             "20 candidates and a 90 MB model download the first time")
    args = parser.parse_args()

    if args.stats:
        print_stats(vault_path=args.vault, db_path=args.db)
    elif args.search:
        results = search_index(args.search, vault_path=args.vault, db_path=args.db,
                               limit=args.limit, rerank=args.rerank)
        print(f"\nHybrid search results for: {args.search!r}")
        for index, result in enumerate(results, 1):
            ranks = []
            if result["lex_rank"] is not None:
                ranks.append(f"lex {result['lex_rank']}")
            if result["vec_rank"] is not None:
                ranks.append(f"vec {result['vec_rank']}")
            if "rerank_score" in result:
                ranks.append(f"ce {result['rerank_score']:.2f}")
            print(
                f"{index}. {result['path']}:{result['start_line']} #{result['heading']} "
                f"(RRF {result['score']:.4f}; {', '.join(ranks)})"
            )
            if result["snippet"]:
                print(f"   {result['snippet']}")
    elif args.check_duplicate or args.check_duplicate_batch:
        return check_duplicate_batch(
            args.check_duplicate_batch or [args.check_duplicate],
            vault_path=args.vault, db_path=args.db, threshold=args.threshold, as_json=args.json,
        )
    elif args.links:
        query_links(args.links, vault_path=args.vault, db_path=args.db)
    else:
        build_index(vault_path=args.vault, db_path=args.db, skip_embeddings=args.skip_embeddings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
