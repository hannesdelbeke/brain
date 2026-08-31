"""Test lift-normalized co-commit scoring against raw weight and the hard
hub-degree threshold, on real co_commit.db data.

Amazon's item-to-item collaborative filtering paper (Linden, Smith & York
2003) found raw co-occurrence counting ("bought together") overweights
popular items - a bestseller (here, a hub note like AGENTS.md) dominates
every association regardless of relevance, the same trap co_commit.py's own
docstring names for its unfiltered top-weight edges. Their fix was not a
threshold: a differential-probability (lift) metric.

    lift(A, B) = P(B|A) / P(B)
               = [weight(A,B) / total_weight(A)] / [total_weight(B) / grand_total]

P(B|A): B's share of A's own co-commit partners, weight-normalized.
P(B): B's share of co-commit weight across the WHOLE graph - B's baseline
popularity, independent of A. A hub note has a huge total_weight(B), so it
needs a correspondingly huge weight(A,B) to still score high lift with any
specific A - this self-normalizes across graph scale, no manually-picked
degree threshold required.

`co_commit.py`'s shipped mitigation for the same problem is a hard cutoff
(`hub_notes()`, degree > threshold dropped from results, default 20)
calibrated for its own 199,783-edge private-vault graph. The robustness retest in
`2026-08-31 other candidate relatedness signals for search reranking.md`
found that threshold does not transfer to smaller graphs at all: meaningless
on co-touch's 3,445 edges (either excludes almost nothing or almost
everything depending on the graph's real degree distribution).

Three variants compared head to head, same evaluation shape as
shared_neighbor_experiment.py (rank_of/wikilink_ground_truth/rrf_fuse_scores
reused directly, not redefined):
    raw       - score(A,B) = weight(A,B), no exclusion
    threshold - score(A,B) = weight(A,B), co_commit.py's own hub_notes() candidates dropped
    lift      - score(A,B) = lift(A,B), no exclusion needed

    python skills/pkm-metadata-indexer/lift_cooccurrence_experiment.py \
        --vault-dir <vault with wikilinks+vectors> --co-commit-db <path> --cc-vault brain
    python skills/pkm-metadata-indexer/lift_cooccurrence_experiment.py --self-check
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm
from recency_prior_experiment import rank_of, wikilink_ground_truth, note_vectors
from shared_neighbor_experiment import rrf_fuse_scores
from co_commit import hub_notes as co_commit_hub_notes
from co_touch import hub_notes as co_touch_hub_notes

VARIANTS = ("raw", "threshold", "lift")
DEFAULT_RRF_KS = (1, 5, 10, 60, 100, 1000)

# co_touch.db's `co_touch` table is schema-compatible with co_commit.db's
# `co_commits` (same note_a/note_b/weight columns, co_touch.py near-copied
# the shape deliberately) - one loader and one hub_notes lookup serve both,
# picked by table name instead of a second near-duplicate script.
HUB_NOTES_BY_TABLE = {"co_commits": co_commit_hub_notes, "co_touch": co_touch_hub_notes}


def load_co_commit_weights(db_path: Path, vault: str = "", table: str = "co_commits"):
    """One pass over the edge table: a symmetric edge-weight dict, plus each
    note's total co-commit weight (sum of its own edges) - the two numbers
    lift needs, read straight from the existing table rather than
    rebuilding edge data from git history again."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault,) if vault else ()
        rows = conn.execute(f"SELECT note_a, note_b, weight FROM {table} {clause}", params).fetchall()
    finally:
        conn.close()
    weights: dict[str, dict[str, float]] = defaultdict(dict)
    totals: dict[str, float] = defaultdict(float)
    for a, b, w in rows:
        weights[a][b] = w
        weights[b][a] = w
        totals[a] += w
        totals[b] += w
    grand_total = sum(totals.values())
    return weights, totals, grand_total


def lift(weight_ab: float, total_a: float, total_b: float, grand_total: float) -> float:
    """P(B|A) / P(B). 0 with no edge or no degree to normalize by."""
    if weight_ab <= 0 or total_a <= 0 or total_b <= 0 or grand_total <= 0:
        return 0.0
    p_b_given_a = weight_ab / total_a
    p_b = total_b / grand_total
    return p_b_given_a / p_b


def score_all(weights, totals, grand_total, paths: list[str], anchor: str,
             variant: str, hubs: set[str] | None = None) -> np.ndarray:
    """variant: 'raw' (plain weight), 'threshold' (plain weight, hub
    candidates zeroed - co_commit.py's own production mechanism, which drops
    a hub from *results*, not from anchor eligibility), 'lift' (self-normalized,
    no exclusion)."""
    anchor_edges = weights.get(anchor, {})
    total_a = totals.get(anchor, 0.0)
    scores = np.zeros(len(paths), dtype=np.float64)
    for i, path in enumerate(paths):
        w = anchor_edges.get(path, 0.0)
        if w <= 0:
            continue
        if variant == "threshold" and hubs and path in hubs:
            continue
        if variant == "lift":
            scores[i] = lift(w, total_a, totals.get(path, 0.0), grand_total)
        else:
            scores[i] = w
    return scores


def run_standalone(vec_paths, vec_index_of, pooled, usable, weights, totals,
                   grand_total, graph_paths, path_in_graph_index, variant, hubs) -> dict:
    """Same shape as shared_neighbor_experiment's standalone block: how well
    the variant alone ranks the true target (not a fair vector comparison,
    a dedicated embedding model should always win alone), plus overlap with
    vector's own top-10 neighbours - the number that actually matters, the
    same way co-commit itself was judged by overlap rather than standalone
    accuracy."""
    ranks, baseline = [], []
    vector_neighbor_sets, variant_neighbor_sets = {}, {}
    for source, target in usable:
        if source not in path_in_graph_index or target not in path_in_graph_index:
            continue
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue
        top_vector = set(np.array(vec_paths)[np.argsort(-vector_scores)[:11]]) - {source}
        vector_neighbor_sets[source] = top_vector

        target_g_index = path_in_graph_index[target]
        anchor_g_index = path_in_graph_index[source]
        scores = score_all(weights, totals, grand_total, graph_paths, source, variant, hubs)
        rank = rank_of(scores, path_in_graph_index, anchor_g_index, target_g_index)
        if rank is not None:
            ranks.append(rank)
            baseline.append(baseline_rank)
        top_variant = set(np.array(graph_paths)[np.argsort(-scores)[:11]]) - {source}
        variant_neighbor_sets[source] = top_variant

    overlaps = [
        len(vector_neighbor_sets[a] & variant_neighbor_sets[a]) / max(1, len(variant_neighbor_sets[a]))
        for a in variant_neighbor_sets if variant_neighbor_sets[a]
    ]
    out = {"variant": variant, "mean_vector_overlap_pct":
           round(100 * float(np.mean(overlaps)), 1) if overlaps else None}
    if not ranks:
        out["error"] = "no usable pairs"
        return out
    mrr = float(np.mean([1 / r for r in ranks]))
    mrr_baseline = float(np.mean([1 / r for r in baseline]))
    out.update({
        "pairs": len(ranks),
        "mean_rank": round(float(np.mean(ranks)), 2),
        "mrr": round(mrr, 4),
        "mrr_vs_vector_baseline_pct": round((mrr / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    })
    return out


def run_fusion(vec_paths, vec_index_of, pooled, usable, weights, totals, grand_total,
              graph_paths, path_in_graph_index, variant, hubs, k: float) -> dict:
    """RRF-fuse the variant's rank list with the vector-rank list - the fair
    "does adding this to vector search help" test, same mechanics as
    shared_neighbor_experiment.run_fusion."""
    candidates = sorted(set(vec_paths) | set(graph_paths))
    cand_index = {p: i for i, p in enumerate(candidates)}
    vec_to_cand = np.array([cand_index.get(p, -1) for p in vec_paths])
    graph_to_cand = np.array([cand_index.get(p, -1) for p in graph_paths])

    baseline_ranks, fused_ranks = [], []
    for source, target in usable:
        if source not in path_in_graph_index or target not in path_in_graph_index:
            continue
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue

        graph_scores = score_all(weights, totals, grand_total, graph_paths, source, variant, hubs)
        v_full = np.full(len(candidates), -1.0, dtype=np.float64)
        v_full[vec_to_cand] = vector_scores
        g_full = np.zeros(len(candidates), dtype=np.float64)
        g_full[graph_to_cand] = graph_scores

        fused = rrf_fuse_scores(v_full, g_full, k)
        anchor_c_index, target_c_index = cand_index[source], cand_index[target]
        fused_rank = rank_of(fused, cand_index, anchor_c_index, target_c_index)
        if fused_rank is None:
            continue
        baseline_ranks.append(baseline_rank)
        fused_ranks.append(fused_rank)

    n = len(baseline_ranks)
    if n == 0:
        return {"variant": variant, "rrf_k": k, "error": "no usable pairs"}
    mrr_baseline = float(np.mean([1 / r for r in baseline_ranks]))
    mrr_fused = float(np.mean([1 / r for r in fused_ranks]))
    improved = sum(1 for b, r in zip(baseline_ranks, fused_ranks) if r < b)
    worsened = sum(1 for b, r in zip(baseline_ranks, fused_ranks) if r > b)
    return {
        "variant": variant, "rrf_k": k, "pairs": n,
        "improved": improved, "worsened": worsened, "unchanged": n - improved - worsened,
        "mrr_baseline": round(mrr_baseline, 4),
        "mrr_fused": round(mrr_fused, 4),
        "mrr_change_pct": round((mrr_fused / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }


def run_compare(vault_dir: Path, db_path: Path, co_commit_db: Path, cc_vault: str,
                sample: int, seed: int, hub_degree: int,
                rrf_ks=DEFAULT_RRF_KS, table: str = "co_commits") -> dict:
    """Load vectors/wikilinks/co-commit weights once, then run all three
    variants (raw, threshold, lift) standalone and at every RRF k - the
    three-way head-to-head the survey note's "wider prior art" section asked
    for, on the same real data for each variant so the comparison is fair."""
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    vec_paths, vec_index_of, pooled = note_vectors(meta, matrix)

    weights, totals, grand_total = load_co_commit_weights(co_commit_db, cc_vault, table)
    graph_paths = sorted(weights)
    path_in_graph_index = {p: i for i, p in enumerate(graph_paths)}
    hubs = HUB_NOTES_BY_TABLE[table](co_commit_db, cc_vault, hub_degree)

    links = wikilink_ground_truth(db_path)
    usable = [(a, b) for a, b in links
             if a in vec_index_of and b in vec_index_of and a in path_in_graph_index]
    rng = np.random.default_rng(seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]

    out = {
        "cc_vault": cc_vault, "co_commit_edges": len(graph_paths) and sum(len(v) for v in weights.values()) // 2,
        "graph_nodes": len(graph_paths), "hubs_at_degree": hub_degree, "hub_count": len(hubs),
        "pairs_sampled": len(usable), "standalone": {}, "fusion": {},
    }
    for variant in VARIANTS:
        v_hubs = hubs if variant == "threshold" else None
        out["standalone"][variant] = run_standalone(
            vec_paths, vec_index_of, pooled, usable, weights, totals, grand_total,
            graph_paths, path_in_graph_index, variant, v_hubs)
        out["fusion"][variant] = [
            run_fusion(vec_paths, vec_index_of, pooled, usable, weights, totals, grand_total,
                      graph_paths, path_in_graph_index, variant, v_hubs, k)
            for k in rrf_ks
        ]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="vault with the wikilinks/vectors to evaluate against, required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault-dir>/.obsidian/pkm_index.db")
    parser.add_argument("--co-commit-db", type=Path, default=Path.home() / ".pkm" / "co_commit.db")
    parser.add_argument("--cc-vault", default="", help="vault identifier inside co_commit.db (e.g. brain, kepano)")
    parser.add_argument("--table", choices=["co_commits", "co_touch"], default="co_commits",
                        help="co_touch.db's co_touch table is schema-compatible, pass this to reuse "
                             "the same lift math and comparison against co_touch.py's own hub_notes()")
    parser.add_argument("--sample", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--hub-degree", type=int, default=20,
                        help="co_commit.py's own threshold default, used for the 'threshold' variant")
    parser.add_argument("--rrf-ks", type=float, nargs="+", default=list(DEFAULT_RRF_KS))
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)
    import json
    result = run_compare(vault_dir, db_path, args.co_commit_db, args.cc_vault,
                         args.sample, args.seed, args.hub_degree, tuple(args.rrf_ks), args.table)
    print(json.dumps(result, indent=1))


def self_check():
    # A popular hub H co-occurs with 5 different notes at weight 5 each
    # (raw-weight winner). X and Y co-occur ONLY with each other, at a lower
    # raw weight of 3. By construction, lift must invert this: H's high
    # total_weight (25) makes it "expected" to co-occur with almost anything,
    # so any single partnership of H's contributes little differential
    # information; X and Y's total_weight (3 each) is entirely explained by
    # this one pairing, so it is much more informative despite the lower raw
    # count - exactly Amazon's "hub inflation" bug and its fix.
    weights = {
        "H": {"A": 5.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 5.0},
        "A": {"H": 5.0}, "B": {"H": 5.0}, "C": {"H": 5.0}, "D": {"H": 5.0}, "E": {"H": 5.0},
        "X": {"Y": 3.0}, "Y": {"X": 3.0},
    }
    totals = {"H": 25.0, "A": 5.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 5.0, "X": 3.0, "Y": 3.0}
    grand_total = sum(totals.values())  # 56

    lift_h_a = lift(weights["H"]["A"], totals["H"], totals["A"], grand_total)
    lift_x_y = lift(weights["X"]["Y"], totals["X"], totals["Y"], grand_total)
    raw_h_a, raw_x_y = weights["H"]["A"], weights["X"]["Y"]

    assert raw_h_a > raw_x_y, "sanity: raw weight ranks the hub pairing higher (5 > 3)"
    assert lift_x_y > lift_h_a, (
        f"lift must invert raw weight's ranking: rare specific pairing (lift={lift_x_y:.2f}) "
        f"should score higher than the popular hub's pairing (lift={lift_h_a:.2f})"
    )
    assert lift_h_a < 3.0, "a hub's own pairing should sit close to background (lift near 1-3x), not far above it"
    assert lift_x_y > 15.0, "a pairing fully explained by one rare partner should score far above baseline"

    paths = ["H", "A", "B", "C", "D", "E", "X", "Y"]
    scores_raw_from_h = score_all(weights, totals, grand_total, paths, "H", "raw")
    scores_lift_from_h = score_all(weights, totals, grand_total, paths, "H", "lift")
    index_of = {p: i for i, p in enumerate(paths)}
    # raw weight treats every H-partner identically (all 5.0); lift does too
    # here since every partner has equal total_weight - but the interesting
    # comparison is cross-anchor, done above via lift_h_a vs lift_x_y.
    assert scores_raw_from_h[index_of["A"]] == 5.0
    assert scores_lift_from_h[index_of["A"]] == lift_h_a

    # threshold variant: H has degree 5 (5 distinct partners) - a threshold
    # of 4 makes it a hub, dropped from results entirely.
    hubs = {"H"}
    scores_threshold_from_a = score_all(weights, totals, grand_total, paths, "A", "threshold", hubs)
    assert scores_threshold_from_a[index_of["H"]] == 0.0, "hub excluded under the threshold variant"
    scores_raw_from_a = score_all(weights, totals, grand_total, paths, "A", "raw")
    assert scores_raw_from_a[index_of["H"]] == 5.0, "same edge, unfiltered under the raw variant"

    # End-to-end: load_co_commit_weights reproduces the same totals/grand_total
    # from a real co_commits table (Windows needs the connection closed before
    # the temp dir is removed).
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp) / "test_lift_co_commit.db"
        conn = sqlite3.connect(db)
        with conn:
            conn.execute(
                "CREATE TABLE co_commits (vault TEXT, note_a TEXT, note_b TEXT, weight REAL, "
                "commit_count INTEGER, last_commit TEXT, last_sha TEXT)"
            )
            rows = [("v", "H", "A", 5.0), ("v", "H", "B", 5.0), ("v", "H", "C", 5.0),
                    ("v", "H", "D", 5.0), ("v", "H", "E", 5.0), ("v", "X", "Y", 3.0)]
            conn.executemany(
                "INSERT INTO co_commits VALUES (?, ?, ?, ?, 1, '2026-08-31', 'abc1234')", rows
            )
        conn.close()
        loaded_weights, loaded_totals, loaded_grand_total = load_co_commit_weights(db, "v")
        assert loaded_totals["H"] == 25.0
        assert loaded_totals["X"] == 3.0
        assert loaded_grand_total == grand_total
        assert loaded_weights["H"]["A"] == 5.0 and loaded_weights["A"]["H"] == 5.0

    print("lift_cooccurrence_experiment.py self-check ok")


if __name__ == "__main__":
    main()
