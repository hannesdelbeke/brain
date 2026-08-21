"""Local metadata, section, link, and hybrid search index for a Markdown vault."""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
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
    paths = []
    for root, directories, files in os.walk(vault_dir):
        directories[:] = [directory for directory in directories if directory not in IGNORED_DIRS]
        for filename in files:
            if filename.endswith(".md"):
                paths.append(Path(root) / filename)
    return sorted(paths)


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


def create_embeddings(sections: list[Section], connection: sqlite3.Connection | None = None) -> dict[str, bytes]:
    if not sections:
        return {}
    if not HAS_FASTEMBED:
        raise RuntimeError("fastembed is required for embeddings. Use --skip-embeddings for metadata-only indexing.")

    model = TextEmbedding(model_name=EMBEDDING_MODEL)
    vectors = {}
    batch_size = 128
    for batch_start in range(0, len(sections), batch_size):
        batch = sections[batch_start : batch_start + batch_size]
        batch_rows = []
        for section, vector in zip(batch, model.embed([section.text for section in batch], batch_size=batch_size)):
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
    return vectors


def remove_missing_rows(cursor: sqlite3.Cursor, table: str, key_column: str, seen_values: set[str]) -> int:
    existing_values = {row[0] for row in cursor.execute(f"SELECT {key_column} FROM {table}")}
    stale_values = existing_values - seen_values
    if stale_values:
        cursor.executemany(
            f"DELETE FROM {table} WHERE {key_column} = ?", ((value,) for value in stale_values)
        )
    return len(stale_values)


def build_index(vault_path: str | None = None, db_path: str | None = None, skip_embeddings: bool = False):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    database_file.parent.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()

    connection = sqlite3.connect(database_file)
    try:
        ensure_schema(connection)
        connection.commit()
        existing_by_id, vectors_by_hash = load_vector_cache(connection)
        notes, sections, links, errors = collect_index_data(vault_dir)

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

        generated_vectors = create_embeddings(sections_to_embed, connection=connection) if sections_to_embed else {}
        vectors_by_id.update(generated_vectors)

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

            cursor.execute(
                """
                INSERT INTO index_runs
                (started_at, completed_at, vault_path, status, note_count, section_count, embedding_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )
            run_id = cursor.lastrowid
            if errors:
                cursor.executemany(
                    "INSERT INTO index_errors(run_id, path, stage, message) VALUES (?, ?, ?, ?)",
                    ((run_id, path, stage, message) for path, stage, message in errors),
                )

        print(f"Indexed {len(notes):,} notes, {len(sections):,} sections, and {len(links):,} links.")
        print(
            f"Vectors: {unchanged_vectors:,} unchanged, {reused_vectors:,} reused by hash, "
            f"{len(generated_vectors):,} generated."
        )
        print(f"Removed {removed_notes:,} notes and {removed_sections:,} sections no longer in the vault.")
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


def fts_query(query: str) -> str:
    terms = re.findall(r"\w+", query, flags=re.UNICODE)
    return " OR ".join(f'"{term}"' for term in terms)


def search_index(
    query: str, vault_path: str | None = None, db_path: str | None = None, limit: int = 10
) -> list[dict]:
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    if not database_file.exists():
        print(f"Index database not found at {database_file}. Run indexing first.")
        return []

    connection = sqlite3.connect(database_file)
    try:
        cursor = connection.cursor()
        lexical_results = {}
        query_expression = fts_query(query)
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
        vector_rows = cursor.execute(
            """
            SELECT id, path, heading, start_line, vector
            FROM sections
            WHERE vector IS NOT NULL AND embedding_model = ? AND chunking_version = ?
            """,
            (EMBEDDING_MODEL, CHUNKING_VERSION),
        ).fetchall()
        if vector_rows:
            if not HAS_FASTEMBED:
                print("fastembed is unavailable; returning lexical results only.")
            else:
                matrix = np.vstack([np.frombuffer(row[4], dtype=np.float32) for row in vector_rows])
                model = TextEmbedding(model_name=EMBEDDING_MODEL)
                query_vector = np.asarray(next(model.embed([query])), dtype=np.float32)
                norm = np.linalg.norm(query_vector)
                if norm > 0:
                    query_vector = query_vector / norm
                scores = matrix @ query_vector
                for rank, index in enumerate(np.argsort(-scores)[:50], 1):
                    row = vector_rows[index]
                    vector_results[row[0]] = {
                        "path": row[1],
                        "heading": row[2],
                        "start_line": row[3],
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
        return sorted(results, key=lambda result: -result["score"])[:limit]
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


def check_duplicate(title: str, vault_path: str | None = None, db_path: str | None = None):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    if not database_file.exists():
        print("Index database not found. Run indexing first.")
        return []

    connection = sqlite3.connect(database_file)
    try:
        title_paths = title_matches(connection.cursor(), title)
    finally:
        connection.close()

    semantic_results = search_index(title, vault_path=vault_dir, db_path=database_file, limit=10)
    candidates = {}
    for rank, path in enumerate(title_paths, 1):
        candidates[path] = {"title_rank": rank, "semantic": None}
    for result in semantic_results:
        candidate = candidates.setdefault(result["path"], {"title_rank": None, "semantic": None})
        if candidate["semantic"] is None or result["raw_sim"] > candidate["semantic"]["raw_sim"]:
            candidate["semantic"] = result

    ordered = sorted(
        candidates.items(),
        key=lambda item: (
            item[1]["title_rank"] is None,
            item[1]["title_rank"] or 999,
            -(item[1]["semantic"] or {"raw_sim": -1})["raw_sim"],
        ),
    )[:5]
    print(f"\nPossible existing notes for: {title!r}")
    if not ordered:
        print("No lexical title or semantic candidates found.")
        return []
    for index, (path, evidence) in enumerate(ordered, 1):
        parts = []
        if evidence["title_rank"] is not None:
            parts.append(f"title rank {evidence['title_rank']}")
        if evidence["semantic"] is not None and evidence["semantic"]["raw_sim"] is not None:
            parts.append(f"cosine {evidence['semantic']['raw_sim']:.3f}")
        print(f"  {index}. {path} ({', '.join(parts)})")
    print("Review the candidates before deciding to append, link, merge, or create a distinct note.")
    return ordered


def find_note_paths(cursor: sqlite3.Cursor, note_reference: str) -> list[str]:
    clean_reference = normalise_note_key(note_reference)
    paths = [row[0] for row in cursor.execute("SELECT path FROM notes")]
    exact = [path for path in paths if normalise_note_key(path) == clean_reference]
    if exact:
        return exact
    return [path for path in paths if Path(path).stem.casefold() == Path(clean_reference).name.casefold()]


def query_links(note_reference: str, vault_path: str | None = None, db_path: str | None = None):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
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


def print_stats(vault_path: str | None = None, db_path: str | None = None):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    if not database_file.exists():
        print("Database not found.")
        return

    connection = sqlite3.connect(database_file)
    try:
        cursor = connection.cursor()
        note_count = cursor.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        section_count, vector_count = cursor.execute("SELECT COUNT(*), COUNT(vector) FROM sections").fetchone()
        edge_count = cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        fts_count = cursor.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0]
        title_count = cursor.execute("SELECT COUNT(*) FROM note_titles_fts").fetchone()[0]
        latest_run = cursor.execute(
            """
            SELECT status, completed_at, error_count
            FROM index_runs ORDER BY id DESC LIMIT 1
            """
        ).fetchone()

        print("\n--- PKM Index Stats ---")
        print(f"Database location: {database_file}")
        print(f"Database size:     {database_file.stat().st_size / (1024 * 1024):.2f} MB")
        print(f"Indexed notes:     {note_count:,}")
        print(f"Sections:          {section_count:,}")
        print(f"FTS sections:      {fts_count:,}")
        print(f"Title index rows:  {title_count:,}")
        print(f"Vector embeddings: {vector_count:,} ({EMBEDDING_MODEL})")
        print(f"Link graph edges:  {edge_count:,}")
        if latest_run:
            print(
                f"Latest run:        {latest_run[0]} at {latest_run[1]} "
                f"({latest_run[2]} errors)"
            )
        print("-----------------------\n")
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
    parser.add_argument("--links", type=str, default=None, help="Show inbound and outbound links for a note")
    parser.add_argument("--stats", action="store_true", help="Display database and latest-run stats")
    parser.add_argument("--limit", type=int, default=10, help="Maximum search results")
    args = parser.parse_args()

    if args.stats:
        print_stats(vault_path=args.vault, db_path=args.db)
    elif args.search:
        results = search_index(args.search, vault_path=args.vault, db_path=args.db, limit=args.limit)
        print(f"\nHybrid search results for: {args.search!r}")
        for index, result in enumerate(results, 1):
            ranks = []
            if result["lex_rank"] is not None:
                ranks.append(f"lex {result['lex_rank']}")
            if result["vec_rank"] is not None:
                ranks.append(f"vec {result['vec_rank']}")
            print(
                f"{index}. {result['path']}:{result['start_line']} #{result['heading']} "
                f"(RRF {result['score']:.4f}; {', '.join(ranks)})"
            )
            if result["snippet"]:
                print(f"   {result['snippet']}")
    elif args.check_duplicate:
        check_duplicate(args.check_duplicate, vault_path=args.vault, db_path=args.db)
    elif args.links:
        query_links(args.links, vault_path=args.vault, db_path=args.db)
    else:
        build_index(vault_path=args.vault, db_path=args.db, skip_embeddings=args.skip_embeddings)


if __name__ == "__main__":
    main()
