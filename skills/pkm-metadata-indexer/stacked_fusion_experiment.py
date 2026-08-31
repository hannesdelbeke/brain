"""Test whether stacking several of tonight's tested signals into ONE RRF
fusion (vector + recency + co-commit, or + AA on top) beats adding any single
one of them alone - the interaction-effect check candidates #1 and #3's
individual rejections and recency/co-commit's individual validations could
not see, since each of those tests only ever fused one signal against vector
rank at a time.

Reuses rather than reimplements: `note_vectors`/`rank_of`/`wikilink_ground_
truth`/`gap_hours`/`recency_proximity`/`build_creation_dates` from
recency_prior_experiment.py, and `load_all_edges`/`build_neighbor_sets`/
`score_all`/`rrf_fuse_scores` from shared_neighbor_experiment.py. The only new
machinery is `rrf_fuse_many` (the N-ary generalisation of `rrf_fuse_scores`'s
pairwise RRF - same `1/(k+rank)` per signal, summed over however many are
stacked instead of exactly two) and a co-commit score lookup, since neither
existing script scores co-commit weight as a per-anchor array the way AA/tags
already do for their own graphs.

recency_prior_experiment.py's own docstring is why RRF (not the additive
combine that beat multiplicative for recency alone) is the stacking mechanism
here: "RRF fuses by RANK POSITION instead of rescaling a score... capping a
signal's contribution at 1/k no matter how many temporal rivals exist" - the
property that makes stacking N of them well-defined without re-deriving a
relative lambda between every pair of signals' raw score scales (vector
cosine similarity, a co-commit power-law weight, and a recency gap in hours
are not naturally comparable magnitudes; rank position always is). An
additive variant is included too (--combine add) since the note's own
verdict on recency was that additive, not RRF, was the winning mechanism
there - each signal gets its own lambda instead of sharing one k.

    python skills/pkm-metadata-indexer/stacked_fusion_experiment.py --vault-dir <vault> --sample 500 --rrf-k 60
    python skills/pkm-metadata-indexer/stacked_fusion_experiment.py --vault-dir <vault> --sample 500 --combine add
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm
from recency_prior_experiment import (
    rank_of, wikilink_ground_truth, note_vectors, gap_hours,
    recency_proximity, build_creation_dates,
)
from shared_neighbor_experiment import load_all_edges, build_neighbor_sets, score_all

DEFAULT_CO_COMMIT_DB = Path.home() / ".pkm" / "co_commit.db"
DEFAULT_RECENCY_CACHE = Path.home() / ".pkm" / "recency-experiment-datetimes.json"


def load_cocommit_weights(db_path: Path, vault: str) -> dict[str, dict[str, float]]:
    """Undirected adjacency of co-commit weight, same shape as
    shared_neighbor_experiment.py's neighbour sets but weighted rather than
    a plain set, since co-commit's own signal is the weight itself, not a
    count of shared third notes."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT note_a, note_b, weight FROM co_commits WHERE vault = ?", (vault,)
        ).fetchall()
    finally:
        conn.close()
    adjacency: dict[str, dict[str, float]] = defaultdict(dict)
    for a, b, w in rows:
        adjacency[a][b] = w
        adjacency[b][a] = w
    return adjacency


def co_commit_score_all(adjacency: dict[str, dict[str, float]], paths: list[str], anchor: str) -> np.ndarray:
    edges = adjacency.get(anchor, {})
    scores = np.zeros(len(paths), dtype=np.float64)
    if not edges:
        return scores
    for index, path in enumerate(paths):
        w = edges.get(path)
        if w:
            scores[index] = w
    return scores


def rrf_fuse_many(score_arrays: list[np.ndarray], k: float) -> np.ndarray:
    """N-ary generalisation of shared_neighbor_experiment.py's rrf_fuse_scores:
    every array is a higher-is-better score list over the same candidate index
    space, and every list contributes 1/(k+rank) to the fused total - a
    signal's maximum possible contribution stays capped at 1/k no matter how
    many other signals are stacked alongside it, the same structural guarantee
    the pairwise version has against one candidate rescale swamping another."""
    n = len(score_arrays[0])
    fused = np.zeros(n, dtype=np.float64)
    for scores in score_arrays:
        rank = np.empty(n, dtype=np.float64)
        rank[np.argsort(-scores)] = np.arange(n)
        fused += 1.0 / (k + rank)
    return fused


def run_experiment(vault_dir: Path, db_path: Path, co_commit_db: Path, co_commit_vault: str,
                   dates: dict[str, str], sample: int, seed: int, k: float,
                   tau_hours: float, combine: str, lam_recency: float, lam_cocommit: float,
                   lam_aa: float) -> dict:
    """Standalone signals (vector+recency, vector+co-commit, vector+AA) at the
    same k/sample as the stacked combos below, so "does stacking beat the best
    single addition" is a fair same-sample, same-k comparison rather than a
    comparison against numbers pulled from a different run."""
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    vec_paths, vec_index_of, pooled = note_vectors(meta, matrix)

    edges = load_all_edges(db_path)
    neighbors = build_neighbor_sets(edges)
    co_adjacency = load_cocommit_weights(co_commit_db, co_commit_vault)

    links = wikilink_ground_truth(db_path)
    usable = [(a, b) for a, b in links if a in vec_index_of and b in vec_index_of and a in dates]
    rng = np.random.default_rng(seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]

    combo_names = [
        "recency_only", "cocommit_only", "aa_only",
        "vector+recency+cocommit", "vector+recency+cocommit+aa",
    ]
    ranks: dict[str, list[int]] = {name: [] for name in combo_names}
    baseline_ranks = []

    for source, target in usable:
        anchor_index, target_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_index, target_index)
        if baseline_rank is None:
            continue

        # Recency as a higher-is-better score for RRF ranking (negative gap:
        # a smaller gap ranks first, same ordering gap_hours ascending gives,
        # just reshaped to fit rrf_fuse_many's "higher score wins" contract).
        gaps = np.array([
            gap_hours(dates[source], dates[path]) if path in dates else 1e9
            for path in vec_paths
        ])
        recency_rrf_score = -gaps
        recency_prox = np.array([
            recency_proximity(dates[source], dates.get(path, dates[source]), tau_hours)
            if path in dates else 0.0
            for path in vec_paths
        ])
        cc_scores = co_commit_score_all(co_adjacency, vec_paths, source)
        aa_scores = score_all(neighbors, vec_paths, source, "aa")

        if combine == "rrf":
            signals = {
                "recency_only": rrf_fuse_many([vector_scores, recency_rrf_score], k),
                "cocommit_only": rrf_fuse_many([vector_scores, cc_scores], k),
                "aa_only": rrf_fuse_many([vector_scores, aa_scores], k),
                "vector+recency+cocommit": rrf_fuse_many(
                    [vector_scores, recency_rrf_score, cc_scores], k),
                "vector+recency+cocommit+aa": rrf_fuse_many(
                    [vector_scores, recency_rrf_score, cc_scores, aa_scores], k),
            }
        else:
            # ponytail: co-commit weight has no natural [0,1] scale the way
            # recency_proximity's exp decay does, so this caps it linearly at
            # 5.0 (roughly the top of a focused 2-3-file commit's weight
            # range per co_commit.py's docstring) rather than deriving a real
            # calibration - upgrade path if additive stacking gets pursued
            # further: fit lam_cocommit against real judged pairs instead.
            cc_prox = np.minimum(cc_scores / 5.0, 1.0)
            aa_prox = np.minimum(aa_scores / 5.0, 1.0)
            signals = {
                "recency_only": vector_scores + lam_recency * recency_prox,
                "cocommit_only": vector_scores + lam_cocommit * cc_prox,
                "aa_only": vector_scores + lam_aa * aa_prox,
                "vector+recency+cocommit": (
                    vector_scores + lam_recency * recency_prox + lam_cocommit * cc_prox),
                "vector+recency+cocommit+aa": (
                    vector_scores + lam_recency * recency_prox + lam_cocommit * cc_prox
                    + lam_aa * aa_prox),
            }

        pair_ranks = {
            name: rank_of(scores, vec_index_of, anchor_index, target_index)
            for name, scores in signals.items()
        }
        if any(r is None for r in pair_ranks.values()):
            continue
        baseline_ranks.append(baseline_rank)
        for name, r in pair_ranks.items():
            ranks[name].append(r)

    n = len(baseline_ranks)
    if n == 0:
        return {"error": "no usable pairs"}
    mrr_baseline = float(np.mean([1 / r for r in baseline_ranks]))
    out = {
        "combine": combine, "k_or_tau_hours": k if combine == "rrf" else tau_hours,
        "pairs": n, "mrr_baseline": round(mrr_baseline, 4),
    }
    for name in combo_names:
        mrr = float(np.mean([1 / r for r in ranks[name]]))
        out[name] = {
            "mean_rank": round(float(np.mean(ranks[name])), 2),
            "mrr": round(mrr, 4),
            "mrr_change_pct": round((mrr / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
        }
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--co-commit-db", type=Path, default=DEFAULT_CO_COMMIT_DB)
    parser.add_argument("--co-commit-vault", default="brain",
                        help="vault identifier co_commit.py stored this corpus under")
    parser.add_argument("--recency-cache", type=Path, default=DEFAULT_RECENCY_CACHE)
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rrf-k", type=float, default=60.0, help="RRF k, ignored for --combine add")
    parser.add_argument("--tau", type=float, default=30.0, help="recency decay tau in days, ignored for --combine rrf")
    parser.add_argument("--combine", choices=["rrf", "add"], default="rrf")
    parser.add_argument("--lam-recency", type=float, default=0.5)
    parser.add_argument("--lam-cocommit", type=float, default=0.5)
    parser.add_argument("--lam-aa", type=float, default=0.5)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)

    if args.recency_cache.exists():
        dates = json.loads(args.recency_cache.read_text(encoding="utf-8"))
    else:
        dates = build_creation_dates(vault_dir)
        args.recency_cache.parent.mkdir(parents=True, exist_ok=True)
        args.recency_cache.write_text(json.dumps(dates), encoding="utf-8")

    result = run_experiment(
        vault_dir, db_path, args.co_commit_db, args.co_commit_vault, dates,
        args.sample, args.seed, args.rrf_k, args.tau * 24, args.combine,
        args.lam_recency, args.lam_cocommit, args.lam_aa,
    )
    print(json.dumps(result, indent=1))


def self_check():
    # rrf_fuse_many with two arrays must reproduce shared_neighbor_experiment's
    # own pairwise rrf_fuse_scores exactly - it's the same formula, just summed
    # over a list instead of two named arguments.
    from shared_neighbor_experiment import rrf_fuse_scores
    a = np.array([0.9, 0.1, 0.5])
    b = np.array([0.2, 0.8, 0.4])
    assert np.allclose(rrf_fuse_many([a, b], k=10.0), rrf_fuse_scores(a, b, k=10.0))

    # Stacking a THIRD array that unambiguously favours candidate 2 (index 1)
    # must be able to move it to the top even though it trails on both a and
    # b - the interaction effect this script exists to detect.
    c = np.array([0.0, 0.99, 0.1])
    two_way = rrf_fuse_many([a, b], k=1.0)
    three_way = rrf_fuse_many([a, b, c], k=1.0)
    assert np.argmax(two_way) != 1
    assert np.argmax(three_way) == 1

    adjacency = {"x": {"y": 3.5}, "y": {"x": 3.5}}
    scores = co_commit_score_all(adjacency, ["x", "y", "z"], "x")
    assert scores[0] == 0.0 and scores[1] == 3.5 and scores[2] == 0.0
    print("self-check ok")


if __name__ == "__main__":
    main()
