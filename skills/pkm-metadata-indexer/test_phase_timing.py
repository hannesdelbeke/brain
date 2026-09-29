#!/usr/bin/env python3
"""Instrument search_index to time each phase and identify the cold latency cause."""

import sys
import time
import sqlite3
from pathlib import Path
import numpy as np

# Add the indexer directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import index_pkm_meta as pkm

def search_index_instrumented(query: str, db_path: str, limit: int = 10):
    """Instrumented version of search_index that times each phase."""
    timings = {}

    # Phase 0: Setup
    t0 = time.perf_counter()
    database_file = Path(db_path).resolve()
    if not database_file.exists():
        print(f"Index database not found at {database_file}")
        return [], timings
    timings["setup"] = (time.perf_counter() - t0) * 1000

    # Phase 1: SQLite connection open
    t0 = time.perf_counter()
    connection = sqlite3.connect(database_file, timeout=60.0)
    cursor = connection.cursor()
    timings["sqlite_connect"] = (time.perf_counter() - t0) * 1000

    try:
        # Phase 2: Lexical search (FTS)
        t0 = time.perf_counter()
        lexical_results = {}
        query_expression = pkm.fts_query(query, cursor)
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
        timings["fts_search"] = (time.perf_counter() - t0) * 1000

        # Phase 3: Load vectors
        t0 = time.perf_counter()
        meta, matrix = pkm.load_vectors(cursor)
        timings["load_vectors"] = (time.perf_counter() - t0) * 1000

        # Phase 4: Get embedding model
        t0 = time.perf_counter()
        model = pkm.get_embedding_model(pkm.QUERY_PROVIDERS, pkm.QUERY_THREADS)
        timings["get_model"] = (time.perf_counter() - t0) * 1000

        # Phase 5: Embed query
        t0 = time.perf_counter()
        query_vector = np.asarray(
            next(model.embed([pkm.QUERY_INSTRUCTION + query])), dtype=np.float32
        )
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        timings["embed_query"] = (time.perf_counter() - t0) * 1000

        # Phase 6: Vector search (cosine similarity)
        t0 = time.perf_counter()
        scores = matrix @ query_vector
        top_indices = np.argsort(-scores)[:50]
        timings["vector_search"] = (time.perf_counter() - t0) * 1000

        # Phase 7: Build results
        t0 = time.perf_counter()
        vector_results = {}
        for rank, index in enumerate(top_indices, 1):
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
                    "raw_sim": semantic.get("raw_sim") if semantic else None,
                    "snippet": lexical.get("snippet") if lexical else None,
                }
            )
        results.sort(key=lambda x: x["score"], reverse=True)
        timings["build_results"] = (time.perf_counter() - t0) * 1000

        return results[:limit], timings
    finally:
        connection.close()


def main():
    db_path = "/Users/h/Documents/GitHub/FortisPkm/.obsidian/pkm_index.db"

    # Warm run
    print("=== WARM RUN (back-to-back) ===")
    for i in range(2):
        results, timings = search_index_instrumented("test query warm", db_path, limit=5)
        total = sum(timings.values())
        print(f"\nRun {i+1}: Total = {total:.1f}ms")
        for phase, ms in timings.items():
            print(f"  {phase:20s}: {ms:7.1f}ms ({ms/total*100:5.1f}%)")

    # Wait
    print("\n=== WAITING 15 seconds ===")
    time.sleep(15)

    # Cold run
    print("\n=== COLD RUN (after 15s idle) ===")
    results, timings = search_index_instrumented("test query cold", db_path, limit=5)
    total = sum(timings.values())
    print(f"\nTotal = {total:.1f}ms")
    for phase, ms in timings.items():
        print(f"  {phase:20s}: {ms:7.1f}ms ({ms/total*100:5.1f}%)")

    # Immediate warm run
    print("\n=== WARM RUN (immediately after) ===")
    results, timings = search_index_instrumented("test query warm again", db_path, limit=5)
    total = sum(timings.values())
    print(f"\nTotal = {total:.1f}ms")
    for phase, ms in timings.items():
        print(f"  {phase:20s}: {ms:7.1f}ms ({ms/total*100:5.1f}%)")


if __name__ == "__main__":
    main()
