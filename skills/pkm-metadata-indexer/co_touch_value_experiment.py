"""Test whether session co-touch adds value on its own, separate from whether
it is redundant with co-commit.

`co_touch.py`'s own verdict ("tested, rejected") only measured one thing: raw
edge-set overlap with `co_commit.py` (87.9%, "redundant with co-commit"). That
verdict presupposes the reader has a co-commit signal to be redundant with -
true for anyone who edits the vault through git, false for anyone who only
ever touches notes through a Claude Code session and never commits. For that
reader the only question that matters is the one candidates #1 and #3 in
"other candidate relatedness signals for search reranking" were both put
through and co-touch never was: does it improve ranking over vector search
alone, on its own terms, against real wikilinks - the same standalone-MRR,
RRF-fusion-sweep, and overlap-with-vector methodology, just scoring candidates
from co_touch's own stored edge weights instead of a live graph metric.

    AA (candidate #1):     standalone MRR -8.24% vs vector, fused never positive at any k, overlap 22.5%
    tags (candidate #3):   standalone MRR -84.3% vs vector, fused never positive at any k, overlap 5.7%
    co-commit (validated): overlap 1.7% - genuinely different from what vector already captures
    co-touch (this file):  the same three numbers, for the first time

Same evaluation as shared_neighbor_experiment.py and tags_overlap_experiment.py,
both of which reuse recency_prior_experiment.py's rank_of/wikilink_ground_truth/
note_vectors: explicit [[wikilinks]] as ground truth (no LLM judge available),
standalone MRR, RRF-fusion against vector rank swept over k, and a standalone
overlap % with vector's top neighbours - the number that actually decided
candidates #1 and #3, not their headline MRR.

Scoring here is a straight edge-weight lookup into co_touch.py's own database
(`score_all()` below), not a live graph computation - the "own edge weights"
instruction this file was built to satisfy, as opposed to shared_neighbor's
Adamic-Adar/Jaccard which recompute a metric over the wikilink graph on the
fly. Whatever co_touch.py itself would say a pair is worth is exactly what
gets scored here.

The vault under test has to be the private private-vault root, not `public/`:
co_touch.db's edges were built with `--vault-dir <private-vault root> --vault
private-vault` (paths like `AGENTS.md`, `home assistant/...`), so the vector index
and wikilink ground truth have to come from that same root's own
`.obsidian/pkm_index.db`, not the public vault's - a mismatched corpus would
silently score every pair 0 for lacking any shared paths at all.

    python skills/pkm-metadata-indexer/co_touch_value_experiment.py --vault-dir <private-vault root> --sample 500
    python skills/pkm-metadata-indexer/co_touch_value_experiment.py --vault-dir <private-vault root> --fuse-rrf-k 60
    python skills/pkm-metadata-indexer/co_touch_value_experiment.py --vault-dir <private-vault root> --exclude-hubs
    python skills/pkm-metadata-indexer/co_touch_value_experiment.py --self-check
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm
from recency_prior_experiment import rank_of, wikilink_ground_truth, note_vectors
from shared_neighbor_experiment import rrf_fuse_scores
from co_touch import DEFAULT_DB as DEFAULT_CO_TOUCH_DB, hub_notes as co_touch_hub_notes


def load_co_touch_edges(db_path: Path, vault: str = "") -> dict[str, dict[str, float]]:
    """Symmetric adjacency read straight from co_touch's stored weights.

    Unlike shared_neighbor_experiment.py's score_all(), which derives
    Adamic-Adar/Jaccard live from the wikilink graph, there is no metric to
    recompute here - co_touch.py already did the power-law weighting and
    incremental scan, so this is just "what does that table already say."
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault,) if vault else ()
        rows = conn.execute(f"SELECT note_a, note_b, weight FROM co_touch {clause}", params).fetchall()
    finally:
        conn.close()
    adjacency: dict[str, dict[str, float]] = defaultdict(dict)
    for a, b, weight in rows:
        adjacency[a][b] = weight
        adjacency[b][a] = weight
    return adjacency


def score_all(adjacency: dict[str, dict[str, float]], paths: list[str], anchor: str,
             hubs: frozenset[str] = frozenset()) -> np.ndarray:
    """Same shape as shared_neighbor_experiment.py's score_all(): a full score
    vector over `paths` for one anchor. `hubs` mirrors co_commit.py's
    query_associations(exclude_hubs=True) - a hub candidate is forced to 0
    rather than left at whatever weight it accumulated, since a hub note
    (AGENTS.md, a catalog note) is the thing hub-exclusion exists to stop from
    being recommended at all, not just downweighted.
    """
    anchor_edges = adjacency.get(anchor, {})
    scores = np.zeros(len(paths), dtype=np.float64)
    if not anchor_edges:
        return scores
    for index, path in enumerate(paths):
        if path in hubs:
            continue
        scores[index] = anchor_edges.get(path, 0.0)
    return scores


def run_experiment(db_path: Path, co_touch_db: Path, touch_vault: str, sample: int, seed: int,
                   fuse_rrf_k: float | None = None, exclude_hubs: bool = False,
                   hub_degree: int = 20) -> dict:
    """Standalone mode (fuse_rrf_k=None): how well co_touch's own edge weights
    alone rank the true wikilink target, and how much its top neighbours
    overlap with vector's - NOT a fair comparison to vector-only ranking (a
    dedicated embedding model should always win alone), the overlap number is
    what matters here, the same way co-commit, AA and tag-Jaccard were all
    judged by overlap rather than standalone accuracy.

    Fusion mode (fuse_rrf_k set): RRF-fuse co_touch's rank list with the
    vector-rank list, the fair test of whether adding this signal to vector
    search actually helps.
    """
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    vec_paths, vec_index_of, pooled = note_vectors(meta, matrix)

    adjacency = load_co_touch_edges(co_touch_db, touch_vault)
    touch_paths = sorted(adjacency)  # every note that appears in a co-touch edge at all
    path_in_touch_index = {p: i for i, p in enumerate(touch_paths)}
    hubs = co_touch_hub_notes(co_touch_db, touch_vault, hub_degree) if exclude_hubs else frozenset()

    links = wikilink_ground_truth(db_path)
    usable = [(a, b) for a, b in links
             if a in vec_index_of and b in vec_index_of and a in path_in_touch_index]
    rng = np.random.default_rng(seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]

    if fuse_rrf_k is not None:
        return run_fusion(usable, vec_paths, vec_index_of, pooled, adjacency, touch_paths,
                          path_in_touch_index, fuse_rrf_k, hubs)

    ranks, baseline = [], []
    vector_neighbor_sets, touch_neighbor_sets = {}, {}
    for source, target in usable:
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue
        top_vector = set(np.array(vec_paths)[np.argsort(-vector_scores)[:11]]) - {source}
        vector_neighbor_sets[source] = top_vector

        if source not in path_in_touch_index or target not in path_in_touch_index:
            continue
        scores = score_all(adjacency, touch_paths, source, hubs)
        anchor_t_index, target_t_index = path_in_touch_index[source], path_in_touch_index[target]
        rank = rank_of(scores, path_in_touch_index, anchor_t_index, target_t_index)
        if rank is not None:
            ranks.append(rank)
            baseline.append(baseline_rank)
        top_touch = set(np.array(touch_paths)[np.argsort(-scores)[:11]]) - {source}
        touch_neighbor_sets[source] = top_touch

    overlaps = [
        len(vector_neighbor_sets[a] & touch_neighbor_sets[a]) / max(1, len(touch_neighbor_sets[a]))
        for a in touch_neighbor_sets if touch_neighbor_sets[a]
    ]

    out = {
        "pairs_sampled": len(usable),
        "hub_excluded": exclude_hubs,
        "mean_vector_co_touch_overlap_pct": round(100 * float(np.mean(overlaps)), 1) if overlaps else None,
    }
    if not ranks:
        out["co_touch"] = {"error": "no usable pairs"}
        return out
    mrr = float(np.mean([1 / r for r in ranks]))
    mrr_baseline = float(np.mean([1 / r for r in baseline]))
    out["co_touch"] = {
        "pairs": len(ranks),
        "mean_rank": round(float(np.mean(ranks)), 2),
        "mrr": round(mrr, 4),
        "mrr_vs_vector_baseline_pct": round((mrr / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }
    return out


def run_fusion(usable, vec_paths, vec_index_of, pooled, adjacency, touch_paths,
              path_in_touch_index, k: float, hubs: frozenset[str]) -> dict:
    """RRF-fuse co_touch's rank list with the vector-rank list - the fair test
    of whether adding this signal to vector search improves on vector search
    alone, not whether co_touch beats vector search by itself."""
    candidates = sorted(set(vec_paths) | set(touch_paths))
    cand_index = {p: i for i, p in enumerate(candidates)}
    vec_to_cand = np.array([cand_index.get(p, -1) for p in vec_paths])
    touch_to_cand = np.array([cand_index.get(p, -1) for p in touch_paths])

    baseline_ranks, fused_ranks = [], []
    for source, target in usable:
        if source not in path_in_touch_index or target not in path_in_touch_index:
            continue
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue

        touch_scores = score_all(adjacency, touch_paths, source, hubs)
        v_full = np.full(len(candidates), -1.0, dtype=np.float64)
        v_full[vec_to_cand] = vector_scores
        t_full = np.zeros(len(candidates), dtype=np.float64)
        t_full[touch_to_cand] = touch_scores

        fused = rrf_fuse_scores(v_full, t_full, k)
        anchor_c_index, target_c_index = cand_index[source], cand_index[target]
        fused_rank = rank_of(fused, cand_index, anchor_c_index, target_c_index)
        if fused_rank is None:
            continue
        baseline_ranks.append(baseline_rank)
        fused_ranks.append(fused_rank)

    n = len(baseline_ranks)
    if n == 0:
        return {"error": "no usable pairs"}
    mrr_baseline = float(np.mean([1 / r for r in baseline_ranks]))
    mrr_fused = float(np.mean([1 / r for r in fused_ranks]))
    improved = sum(1 for b, r in zip(baseline_ranks, fused_ranks) if r < b)
    worsened = sum(1 for b, r in zip(baseline_ranks, fused_ranks) if r > b)
    return {
        "rrf_k": k, "hub_excluded": bool(hubs), "pairs": n,
        "improved": improved, "worsened": worsened, "unchanged": n - improved - worsened,
        "mean_rank_baseline": round(float(np.mean(baseline_ranks)), 2),
        "mean_rank_fused": round(float(np.mean(fused_ranks)), 2),
        "mrr_baseline": round(mrr_baseline, 4),
        "mrr_fused": round(mrr_fused, 4),
        "mrr_change_pct": round((mrr_fused / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="the private-vault root (co_touch's paths are private-vault-relative, "
                                            "not public/) - required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault-dir>/.obsidian/pkm_index.db")
    parser.add_argument("--co-touch-db", type=Path, default=DEFAULT_CO_TOUCH_DB,
                        help=f"co_touch.py's database (default: {DEFAULT_CO_TOUCH_DB})")
    parser.add_argument("--vault", default="root", help="co_touch vault/corpus identifier "
                                                         "('root' means no filter, e.g. the real 'private-vault' data)")
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fuse-rrf-k", type=float, default=None,
                        help="RRF-fuse co_touch with vector rank at this k, instead of the "
                             "standalone co_touch-vs-vector report")
    parser.add_argument("--exclude-hubs", action="store_true",
                        help="zero out co_touch score for hub notes (co_touch.py's own hub_notes())")
    parser.add_argument("--hub-degree", type=int, default=20,
                        help="co_touch degree threshold above which a note counts as a hub")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)
    touch_vault = args.vault if args.vault != "root" else ""
    result = run_experiment(db_path, args.co_touch_db, touch_vault, args.sample, args.seed,
                            args.fuse_rrf_k, args.exclude_hubs, args.hub_degree)
    print(json.dumps(result, indent=1))


def self_check():
    # score_all: plain edge lookup, symmetric, hub-zeroed, 0 for a missing edge
    adjacency = {"a": {"b": 3.5, "c": 1.2}, "b": {"a": 3.5}, "c": {"a": 1.2}}
    paths = ["a", "b", "c", "d"]
    index_of = {p: i for i, p in enumerate(paths)}
    scores_from_a = score_all(adjacency, paths, "a")
    assert scores_from_a[index_of["b"]] == 3.5, "direct edge weight, not a derived metric"
    assert scores_from_a[index_of["c"]] == 1.2
    assert scores_from_a[index_of["d"]] == 0.0, "no edge at all scores exactly 0"
    scores_hub_excluded = score_all(adjacency, paths, "a", hubs=frozenset({"b"}))
    assert scores_hub_excluded[index_of["b"]] == 0.0, "hub-excluded candidate is forced to 0, not just downweighted"
    assert scores_hub_excluded[index_of["c"]] == 1.2, "a non-hub candidate is untouched by hub exclusion"
    assert np.all(score_all(adjacency, paths, "z") == 0.0), "an anchor with no edges has no opinion about anyone"

    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp) / "test_co_touch.db"
        from co_touch import connect
        conn = connect(db)
        with conn:
            conn.executemany(
                "INSERT INTO co_touch VALUES ('v', ?, ?, ?, 1, '2026-08-31 00:00:00', 's1.jsonl')",
                [("a.md", "b.md", 3.5), ("a.md", "c.md", 1.2)],
            )
        conn.close()  # Windows will not delete the temp dir with the file still open
        loaded = load_co_touch_edges(db, "v")
        assert loaded["a.md"]["b.md"] == 3.5
        assert loaded["b.md"]["a.md"] == 3.5, "adjacency must be symmetric both directions"
        assert loaded["a.md"]["c.md"] == 1.2
        assert "b.md" not in loaded.get("c.md", {}), "no edge between b.md and c.md, so no entry either way"

    print("self-check ok")


if __name__ == "__main__":
    main()
