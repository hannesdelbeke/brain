"""GPU-accelerated semantic search and indexer over deleted Git diff chunks."""

import argparse
import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

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
EMBEDDING_DIM = 384


def get_providers() -> list[str]:
    try:
        import onnxruntime as ort
        available = set(ort.get_available_providers())
        providers = [p for p in ["DmlExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"] if p in available]
        return providers or ["CPUExecutionProvider"]
    except Exception:
        return ["CPUExecutionProvider"]


def find_vault_root() -> Path:
    curr = Path.cwd().resolve()
    for parent in [curr, *curr.parents]:
        if (parent / ".obsidian").exists() or (parent / ".git").exists():
            return parent
    return curr


def ensure_db_schema(conn: sqlite3.Connection):
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=60000;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS git_history_chunks (
            id TEXT PRIMARY KEY,
            sha TEXT NOT NULL,
            date TEXT NOT NULL,
            author TEXT NOT NULL,
            path TEXT NOT NULL,
            snippet TEXT NOT NULL,
            vector BLOB NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gh_sha ON git_history_chunks(sha);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gh_path ON git_history_chunks(path);")
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS git_history_fts USING fts5(
                chunk_id UNINDEXED,
                snippet,
                tokenize='unicode61'
            )
            """
        )
    except sqlite3.OperationalError:
        pass


def is_meaningful_deleted_line(line: str) -> bool:
    content = line.strip()
    if len(content) < 12:
        return False
    # Skip pure metadata lines and symbols
    if content.startswith(("---", "sentiment-hash:", "created:", "energy:", "sentiment:", "sentiment-label:", "aliases:", "tags:")):
        return False
    if content.startswith("- ") and len(content) < 15:
        return False
    return True


def extract_deleted_chunks(vault_dir: Path, since: str | None = None, until: str | None = None, author: str | None = None):
    cmd = ["git", "-C", str(vault_dir), "log", "-p", "-U0", "--date=iso", "-M", "-C", "--", "*.md"]
    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])
    if author:
        cmd.extend([f"--author={author}"])

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, errors="ignore")
    sha, date, commit_author, path = None, None, None, None
    curr_lines = []

    for line in proc.stdout:
        if line.startswith("commit "):
            if curr_lines and sha and path:
                text = "\n".join(curr_lines).strip()
                if len(text) > 30:
                    chunk_id = hashlib.sha256(f"{sha}:{path}:{text}".encode("utf-8")).hexdigest()
                    yield chunk_id, sha, date, commit_author or "Unknown", path, text
                curr_lines = []
            sha = line.split()[1]
        elif line.startswith("Author:"):
            commit_author = line[7:].strip()
        elif line.startswith("Date:"):
            date = line[5:].strip()
        elif line.startswith("--- a/"):
            if curr_lines and sha and path:
                text = "\n".join(curr_lines).strip()
                if len(text) > 30:
                    chunk_id = hashlib.sha256(f"{sha}:{path}:{text}".encode("utf-8")).hexdigest()
                    yield chunk_id, sha, date, commit_author or "Unknown", path, text
                curr_lines = []
            path = line[6:].strip()
        elif line.startswith("-") and not line.startswith("---"):
            content = line[1:].strip()
            if is_meaningful_deleted_line(content):
                curr_lines.append(content)
        elif curr_lines and not line.startswith("-"):
            text = "\n".join(curr_lines).strip()
            if len(text) > 30 and sha and path:
                chunk_id = hashlib.sha256(f"{sha}:{path}:{text}".encode("utf-8")).hexdigest()
                yield chunk_id, sha, date, commit_author or "Unknown", path, text
            curr_lines = []

    if curr_lines and sha and path:
        text = "\n".join(curr_lines).strip()
        if len(text) > 30:
            chunk_id = hashlib.sha256(f"{sha}:{path}:{text}".encode("utf-8")).hexdigest()
            yield chunk_id, sha, date, commit_author or "Unknown", path, text


def build_git_index(vault_dir: Path, db_path: Path, since: str | None = None, until: str | None = None, author: str | None = None):
    if not HAS_FASTEMBED:
        print("fastembed is required to build embeddings. Please install fastembed.", file=sys.stderr)
        return

    conn = sqlite3.connect(db_path, timeout=60.0)
    ensure_db_schema(conn)

    existing_ids = {row[0] for row in conn.execute("SELECT id FROM git_history_chunks").fetchall()}
    print(f"Scanning Git history (Found {len(existing_ids):,} existing indexed chunks)...", flush=True)

    chunks_to_embed = []
    seen_ids = set()
    for chunk_id, sha, date, commit_author, path, text in extract_deleted_chunks(vault_dir, since, until, author):
        if chunk_id in seen_ids or chunk_id in existing_ids:
            continue
        seen_ids.add(chunk_id)
        chunks_to_embed.append((chunk_id, sha, date, commit_author, path, text))

    print(f"Found {len(chunks_to_embed):,} new deleted text chunks to embed.", flush=True)
    if not chunks_to_embed:
        print("Git history index is already up to date.")
        conn.close()
        return

    providers = get_providers()
    print(f"Loading embedding model '{EMBEDDING_MODEL}' using providers: {providers}...", flush=True)
    try:
        model = TextEmbedding(model_name=EMBEDDING_MODEL, providers=providers)
    except Exception as e:
        print(f"Provider load failed ({e}), falling back to CPU...", flush=True)
        model = TextEmbedding(model_name=EMBEDDING_MODEL, providers=["CPUExecutionProvider"])

    batch_size = 32  # Stable batch size for DirectML without driver timeout
    total = len(chunks_to_embed)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = chunks_to_embed[i : i + batch_size]
        texts = [item[5] for item in batch]
        try:
            raw_vectors = list(model.embed(texts, batch_size=batch_size))
        except Exception as embed_err:
            # Fallback to single/CPU mode if GPU batch errors
            print(f"Batch embedding fallback at item {i} ({embed_err})...", flush=True)
            fallback_model = TextEmbedding(model_name=EMBEDDING_MODEL, providers=["CPUExecutionProvider"])
            raw_vectors = list(fallback_model.embed(texts, batch_size=16))

        rows = []
        fts_rows = []
        for (chunk_id, sha, date, commit_author, path, text), vec in zip(batch, raw_vectors):
            vec_arr = np.asarray(vec, dtype=np.float32)
            norm = np.linalg.norm(vec_arr)
            if norm > 0:
                vec_arr = vec_arr / norm
            vec_bytes = vec_arr.tobytes()
            rows.append((chunk_id, sha, date, commit_author, path, text, vec_bytes))
            fts_rows.append((chunk_id, text))

        with conn:
            conn.executemany(
                "INSERT OR IGNORE INTO git_history_chunks VALUES (?, ?, ?, ?, ?, ?, ?)", rows
            )
            try:
                conn.executemany("INSERT OR IGNORE INTO git_history_fts VALUES (?, ?)", fts_rows)
            except sqlite3.OperationalError:
                pass

        inserted += len(rows)
        if inserted % 256 == 0 or inserted == total:
            print(f"Embedded {inserted:,}/{total:,} chunks ({inserted / total * 100:.1f}%)...", flush=True)

    conn.close()
    print(f"Indexing complete. Total {inserted:,} chunks added to {db_path}.")


def search_git_history(query: str, db_path: Path, limit: int = 5):
    if not db_path.exists():
        print(f"Database not found at {db_path}. Run with --build first.", file=sys.stderr)
        return []

    conn = sqlite3.connect(db_path, timeout=60.0)
    cursor = conn.cursor()

    rows = cursor.execute("SELECT id, sha, date, author, path, snippet, vector FROM git_history_chunks").fetchall()
    if not rows:
        print("No historical chunks found in database. Run with --build first.", file=sys.stderr)
        conn.close()
        return []

    providers = get_providers()
    try:
        model = TextEmbedding(model_name=EMBEDDING_MODEL, providers=providers)
        query_vec = np.asarray(next(model.embed([query])), dtype=np.float32)
    except Exception:
        model = TextEmbedding(model_name=EMBEDDING_MODEL, providers=["CPUExecutionProvider"])
        query_vec = np.asarray(next(model.embed([query])), dtype=np.float32)

    norm = np.linalg.norm(query_vec)
    if norm > 0:
        query_vec = query_vec / norm

    matrix = np.vstack([np.frombuffer(row[6], dtype=np.float32) for row in rows])
    scores = matrix @ query_vec
    top_indices = np.argsort(scores)[::-1][:limit]

    results = []
    for idx in top_indices:
        row = rows[idx]
        score = float(scores[idx])
        results.append({
            "score": score,
            "sha": row[1],
            "date": row[2],
            "author": row[3],
            "path": row[4],
            "snippet": row[5],
        })

    conn.close()
    return results


def main():
    parser = argparse.ArgumentParser(description="GPU-accelerated Semantic Search on Git History")
    parser.add_argument("query", nargs="?", help="Semantic query to search for")
    parser.add_argument("--build", action="store_true", help="Build or update the git history embedding index")
    parser.add_argument("--since", help="Filter git log since date (e.g. 2026-01-01)")
    parser.add_argument("--until", help="Filter git log until date")
    parser.add_argument("--author", help="Filter git log by author (e.g. Claude, Gemini)")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return (default: 5)")
    parser.add_argument("--db", help="Path to SQLite index database")

    args = parser.parse_args()
    vault_dir = find_vault_root()
    db_path = Path(args.db).resolve() if args.db else vault_dir / ".obsidian" / "pkm_index.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if args.build or not args.query:
        build_git_index(vault_dir, db_path, since=args.since, until=args.until, author=args.author)
        if not args.query:
            return

    if args.query:
        print(f"\nSearching Git history for: '{args.query}' (limit={args.limit})\n" + "=" * 60)
        results = search_git_history(args.query, db_path, limit=args.limit)
        for i, res in enumerate(results, 1):
            print(f"\n[{i}] Match Score: {res['score']:.4f}")
            print(f"    File:    {res['path']}")
            print(f"    Commit:  {res['sha'][:10]} ({res['date'][:10]}) by {res['author']}")
            print(f"    Restore: git show {res['sha'][:10]}^:\"{res['path']}\"")
            print("    Snippet:")
            for line in res["snippet"].splitlines()[:5]:
                print(f"      | {line}")
            if len(res["snippet"].splitlines()) > 5:
                print("      | ...")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
