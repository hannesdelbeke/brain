"""
Search PKM notes using vector semantic similarity, hybrid search, or graph traversal.
"""

import sys
import sqlite3
import argparse
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

def find_vault_root():
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / ".obsidian").exists() or (parent / ".git").exists():
            return parent
    return current

def semantic_search(query: str, db_path: Path, top_k: int = 10):
    if not HAS_FASTEMBED:
        print("Error: fastembed is required for semantic vector search.")
        return []
        
    model = TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        providers=get_embedding_providers(),
    )
    query_vec = np.array(list(model.embed([query]))[0], dtype=np.float32)
    norm = np.linalg.norm(query_vec)
    if norm > 0:
        query_vec /= norm

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute("SELECT path, heading, start_line, vector FROM sections WHERE vector IS NOT NULL").fetchall()
    conn.close()

    if not rows:
        print("No embedded sections found in index.")
        return []

    results = []
    for path, heading, start_line, vec_blob in rows:
        vec = np.frombuffer(vec_blob, dtype=np.float32)
        score = float(np.dot(vec, query_vec))
        results.append((score, path, heading, start_line))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_k]

def main():
    parser = argparse.ArgumentParser(description="Query vault notes via semantic vector search.")
    parser.add_argument("query", type=str, help="Search query or vibe")
    parser.add_argument("--top", type=int, default=10, help="Number of results to return")
    parser.add_argument("--db", type=str, default=None, help="Path to SQLite database")
    args = parser.parse_args()

    vault_root = find_vault_root()
    db_file = Path(args.db).resolve() if args.db else vault_root / ".obsidian" / "pkm_index.db"

    results = semantic_search(args.query, db_file, top_k=args.top)
    print(f"\n--- Semantic Search Results for: \"{args.query}\" ---")
    for idx, (score, path, heading, line) in enumerate(results, 1):
        print(f"{idx}. [{score:.3f}] {path} (line {line}) -> {heading}")

if __name__ == "__main__":
    main()
