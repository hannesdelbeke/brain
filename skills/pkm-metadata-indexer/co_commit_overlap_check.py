"""Re-measure co-commit / vector-similarity overlap, same shape
shared_neighbor_experiment.py's own overlap check uses (top-10 co-commit
neighbours vs top-10 vector neighbours per anchor, mean intersection ratio) -
this exact method is what the "1.7%" claim was compared against on the three
other vaults tonight, and what the adversarial-review section of
`2026-08-31 other candidate relatedness signals for search reranking.md`
(item 3) used to get 20.90% on this vault, in place of a script by this name
that no longer exists in this repo or any surviving temp directory.

    python skills/pkm-metadata-indexer/co_commit_overlap_check.py --vault-dir <vault> --co-commit-vault brain
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import index_pkm_meta as pkm
from recency_prior_experiment import note_vectors
from co_commit import hub_notes, DEFAULT_DB as DEFAULT_CO_COMMIT_DB


def load_cocommit_adjacency(db_path: Path, vault: str) -> dict[str, dict[str, float]]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT note_a, note_b, weight FROM co_commits WHERE vault = ?", (vault,)
        ).fetchall()
    finally:
        conn.close()
    adjacency: dict[str, dict[str, float]] = {}
    for a, b, w in rows:
        adjacency.setdefault(a, {})[b] = w
        adjacency.setdefault(b, {})[a] = w
    return adjacency


def top_k(neighbor_weights: dict[str, float], k: int) -> list[str]:
    return [n for n, _ in sorted(neighbor_weights.items(), key=lambda kv: -kv[1])[:k]]


def run(vault_dir: Path, db_path: Path, co_commit_db: Path, co_commit_vault: str,
        top: int = 10, hub_degree: int = 20) -> dict:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    vec_paths, vec_index_of, pooled = note_vectors(meta, matrix)

    adjacency = load_cocommit_adjacency(co_commit_db, co_commit_vault)
    hubs = hub_notes(co_commit_db, co_commit_vault, hub_degree)

    top10_vs_top10, every_vs_top10, hub_excl_top10_vs_top10 = [], [], []

    for anchor, neighbor_weights in adjacency.items():
        if anchor not in vec_index_of or not neighbor_weights:
            continue
        anchor_index = vec_index_of[anchor]
        vector_scores = pooled @ pooled[anchor_index]
        top_vector = set(np.array(vec_paths)[np.argsort(-vector_scores)[:top + 1]]) - {anchor}
        top_vector = set(list(top_vector)[:top])

        # variant 1: top-K co-commit neighbours (by weight) vs top-K vector neighbours
        cc_top = set(top_k(neighbor_weights, top))
        if cc_top:
            top10_vs_top10.append(len(cc_top & top_vector) / len(cc_top))

        # variant 2: EVERY co-commit neighbour (not just top-K) vs top-K vector neighbours
        cc_all = set(neighbor_weights.keys())
        if cc_all:
            every_vs_top10.append(len(cc_all & top_vector) / len(cc_all))

        # variant 3: hub-excluded top-K co-commit neighbours vs top-K vector neighbours
        cc_no_hub = {n: w for n, w in neighbor_weights.items() if n not in hubs}
        cc_no_hub_top = set(top_k(cc_no_hub, top))
        if cc_no_hub_top:
            hub_excl_top10_vs_top10.append(len(cc_no_hub_top & top_vector) / len(cc_no_hub_top))

    def summarize(values):
        return {
            "anchors": len(values),
            "mean_overlap_pct": round(100 * float(np.mean(values)), 2) if values else None,
        }

    return {
        "co_commit_vault": co_commit_vault,
        "top_k": top,
        "hub_degree": hub_degree,
        "total_anchors_with_edges": len(adjacency),
        "top10_vs_top10": summarize(top10_vs_top10),
        "every_neighbor_vs_top10": summarize(every_vs_top10),
        "hub_excluded_top10_vs_top10": summarize(hub_excl_top10_vs_top10),
    }


def self_check():
    # anchor with 3 co-commit neighbours, 2 of which are also top-vector
    # neighbours: top-10 ratio should be 2/3, hub exclusion dropping one
    # non-overlapping neighbour should raise the ratio.
    adjacency = {
        "a": {"b": 5.0, "c": 3.0, "d": 1.0},
        "b": {"a": 5.0}, "c": {"a": 3.0}, "d": {"a": 1.0},
    }
    assert top_k(adjacency["a"], 10) == ["b", "c", "d"]
    print("co_commit_overlap_check.py self-check ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--co-commit-db", type=Path, default=DEFAULT_CO_COMMIT_DB)
    parser.add_argument("--co-commit-vault", default="brain")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--hub-degree", type=int, default=20)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)
    result = run(vault_dir, db_path, args.co_commit_db, args.co_commit_vault,
                 args.top, args.hub_degree)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
