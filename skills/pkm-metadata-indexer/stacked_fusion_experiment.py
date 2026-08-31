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
    python skills/pkm-metadata-indexer/stacked_fusion_experiment.py --vault-dir <vault> --calibrate --z-hub-degree 20

`--z-hub-degree` forwards straight to `score_all`'s AA term (see that
function's docstring in shared_neighbor_experiment.py) - the shared-neighbor
hub cutoff built for the game-portfolio same-batch/same-template false
positive. Off (None) by default, same backward-compatible convention as
`shared_neighbor_experiment.py` itself.
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
                   lam_aa: float, z_hub_degree: int | None = None) -> dict:
    """Standalone signals (vector+recency, vector+co-commit, vector+AA) at the
    same k/sample as the stacked combos below, so "does stacking beat the best
    single addition" is a fair same-sample, same-k comparison rather than a
    comparison against numbers pulled from a different run.

    `z_hub_degree`: passed straight through to `shared_neighbor_experiment.py`'s
    `score_all` for the AA term only - same hard cutoff on the shared-neighbor
    z's own degree that script's vault-b false-positive fix added. Default None
    (off), fully backward compatible - see that script's docstring for why."""
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
        aa_scores = score_all(neighbors, vec_paths, source, "aa", z_hub_degree=z_hub_degree)

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


# Grid for the calibration pass below. The by-inspection run this calibrates
# (lam_recency=0.05, lam_cocommit=0.2, lam_aa=0.02) sits inside all three
# ranges, at the same tau=30d - the grid exists to check whether inspection
# happened to land near the real optimum or just somewhere positive, not to
# retest a single already-tried point.
#
# lam_cocommit's range looks lopsided next to the other two because it is:
# an initial 0.05-0.4 grid (matching this file's own docstring survey) pinned
# its winner to the top edge (0.4) on every seed tried, and a manual sweep
# afterward found the real calib-MRR peak between 3 and 10 - roughly an order
# of magnitude past where the by-inspection run and the first grid both
# guessed. cc_prox is capped at 1.0 (see build_pair_signals), so a lambda
# this size only ever amplifies the sparse set of candidates that already
# have a real co-commit edge, not every candidate - unlike lam_recency, whose
# proximity term is a dense per-candidate decay, which is why its own optimum
# stays small and the two lambdas are not on a comparable scale.
LAM_RECENCY_GRID = [0.02, 0.05, 0.08, 0.11, 0.15]
LAM_COCOMMIT_GRID = [0.05, 0.1, 0.2, 0.4, 0.8, 1.5, 3.0, 5.0, 10.0, 15.0]
LAM_AA_GRID = [0.02, 0.05, 0.1, 0.15, 0.2, 0.3]

# The recency term calibrated here uses the SAME hard-cutoff mechanism
# searchd.py's own `&recency=1` already ships and validated independently
# (mode=hard, tau=6h, lambda=0.05, +8.60% MRR) - not the smooth exponential
# decay `run_experiment`'s by-inspection stacking check above used (tau=30
# days). Calibrating a lambda against one recency shape and wiring it onto a
# different one would not actually transfer; this mirrors searchd.py's
# RECENCY_TAU_HOURS so the fusion route below can reuse its exact boost
# rather than invent a second, unvalidated recency implementation.
FUSION_RECENCY_TAU_HOURS = 6.0


def build_pair_signals(usable: list[tuple[str, str]], vec_paths: list[str],
                       vec_index_of: dict, pooled: np.ndarray, dates: dict,
                       co_adjacency: dict, neighbors: dict,
                       recency_tau_hours: float = FUSION_RECENCY_TAU_HOURS,
                       recency_mode: str = "hard",
                       z_hub_degree: int | None = None) -> list[dict]:
    """Precompute every per-pair signal array ONCE, so the lambda grid search
    below only ever does a cheap weighted sum + argsort per combo, instead of
    redoing a matrix multiply, a co-commit lookup and an Adamic-Adar pass per
    grid point - the grid is 300 combos, and recomputing those per combo per
    pair would be the actual bottleneck the grid search waits on, not the
    arithmetic it exists to try.

    `z_hub_degree`: forwarded to `score_all` for the AA term - see
    `run_experiment`'s docstring. Default None, unaffected unless a caller
    (currently only `run_calibration`) sets it."""
    pairs = []
    for source, target in usable:
        anchor_index, target_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_index, target_index)
        if baseline_rank is None:
            continue
        recency_prox = np.array([
            recency_proximity(dates[source], dates.get(path, dates[source]),
                              recency_tau_hours, recency_mode)
            if path in dates else 0.0
            for path in vec_paths
        ])
        cc_scores = co_commit_score_all(co_adjacency, vec_paths, source)
        aa_scores = score_all(neighbors, vec_paths, source, "aa", z_hub_degree=z_hub_degree)
        pairs.append({
            "anchor_index": anchor_index, "target_index": target_index,
            "baseline_rank": baseline_rank,
            "vector_scores": vector_scores,
            "recency_prox": recency_prox,
            # ponytail: same linear cap the by-inspection additive run already
            # used - co-commit/AA have no natural [0,1] scale the way
            # recency_proximity's exp decay does. Upgrade path: fit a real
            # scale against judged pairs if this stops being good enough.
            "cc_prox": np.minimum(cc_scores / 5.0, 1.0),
            "aa_prox": np.minimum(aa_scores / 5.0, 1.0),
        })
    return pairs


def mrr_at_lambdas(pairs: list[dict], vec_index_of: dict, lam_recency: float = 0.0,
                   lam_cocommit: float = 0.0, lam_aa: float = 0.0) -> float | None:
    ranks = []
    for p in pairs:
        scores = (p["vector_scores"] + lam_recency * p["recency_prox"]
                 + lam_cocommit * p["cc_prox"] + lam_aa * p["aa_prox"])
        r = rank_of(scores, vec_index_of, p["anchor_index"], p["target_index"])
        if r is not None:
            ranks.append(r)
    return float(np.mean([1 / r for r in ranks])) if ranks else None


def grid_search(pairs: list[dict], vec_index_of: dict) -> dict:
    """Best lambda combo per stack, by calibration-set MRR alone: three single-
    signal additions (each its own lambda calibrated, not the 0.5-for-
    everything by-inspection default), the 3-way stack (recency+co-commit),
    and the 4-way stack (+AA). Never looks at the holdout set."""
    winners = {}

    def best_over(label: str, combos: list[dict]):
        scored = [(mrr, lam) for lam in combos
                 if (mrr := mrr_at_lambdas(pairs, vec_index_of, **lam)) is not None]
        scored.sort(key=lambda t: -t[0])
        winners[label] = {"lambdas": scored[0][1], "calib_mrr": round(scored[0][0], 4)}

    best_over("recency_only", [{"lam_recency": v} for v in LAM_RECENCY_GRID])
    best_over("cocommit_only", [{"lam_cocommit": v} for v in LAM_COCOMMIT_GRID])
    best_over("aa_only", [{"lam_aa": v} for v in LAM_AA_GRID])
    best_over("stack3_recency_cocommit", [
        {"lam_recency": r, "lam_cocommit": c}
        for r in LAM_RECENCY_GRID for c in LAM_COCOMMIT_GRID])
    best_over("stack4_recency_cocommit_aa", [
        {"lam_recency": r, "lam_cocommit": c, "lam_aa": a}
        for r in LAM_RECENCY_GRID for c in LAM_COCOMMIT_GRID for a in LAM_AA_GRID])
    return winners


def run_calibration(db_path: Path, co_commit_db: Path, co_commit_vault: str,
                    dates: dict, sample: int, split_seed: int, split_frac: float,
                    z_hub_degree: int | None = None) -> dict:
    """Grid search on a calibration fold, real numbers on a held-out fold it
    never touched - the gap the by-inspection stacked-fusion finding could not
    close, since its lambdas were "chosen by inspection, not fit against judged
    pairs" (see the survey note). Splitting `usable` before scoring anything,
    with a seeded shuffle, is what keeps the calibration set and the holdout
    set from ever being the same pairs.

    `z_hub_degree`: forwarded to both the calibration and holdout fold's AA
    term (see `run_experiment`'s docstring) - both folds must use the same
    cutoff, the same way they already share `recency_tau_hours`/`recency_mode`,
    or the comparison stops being apples-to-apples."""
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
    rng = np.random.default_rng(split_seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]
    order = rng.permutation(len(usable))
    cut = int(len(order) * split_frac)
    calib_raw = [usable[i] for i in order[:cut]]
    holdout_raw = [usable[i] for i in order[cut:]]

    calib = build_pair_signals(calib_raw, vec_paths, vec_index_of, pooled, dates,
                               co_adjacency, neighbors, z_hub_degree=z_hub_degree)
    holdout = build_pair_signals(holdout_raw, vec_paths, vec_index_of, pooled, dates,
                                 co_adjacency, neighbors, z_hub_degree=z_hub_degree)
    if not calib or not holdout:
        return {"error": "not enough usable pairs after the calibration/holdout split"}

    winners = grid_search(calib, vec_index_of)
    calib_baseline = float(np.mean([1 / p["baseline_rank"] for p in calib]))
    holdout_baseline = float(np.mean([1 / p["baseline_rank"] for p in holdout]))

    out = {
        "split_seed": split_seed, "split_frac": split_frac,
        "recency_tau_hours": FUSION_RECENCY_TAU_HOURS, "recency_mode": "hard",
        "z_hub_degree": z_hub_degree,
        "calib_pairs": len(calib), "holdout_pairs": len(holdout),
        "calib_baseline_mrr": round(calib_baseline, 4),
        "holdout_baseline_mrr": round(holdout_baseline, 4),
        "winners": {},
    }
    for name, info in winners.items():
        holdout_mrr = mrr_at_lambdas(holdout, vec_index_of, **info["lambdas"])
        out["winners"][name] = {
            "lambdas": info["lambdas"],
            "calib_mrr": info["calib_mrr"],
            "calib_change_pct": round((info["calib_mrr"] / calib_baseline - 1) * 100, 2),
            "holdout_mrr": round(holdout_mrr, 4) if holdout_mrr is not None else None,
            "holdout_change_pct": (round((holdout_mrr / holdout_baseline - 1) * 100, 2)
                                   if holdout_mrr else None),
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
    parser.add_argument("--calibrate", action="store_true",
                        help="grid search lambdas on a calibration fold, report MRR on a held-out "
                             "fold the grid search never saw, instead of running one fixed combo")
    parser.add_argument("--split-frac", type=float, default=0.6,
                        help="fraction of usable pairs kept for calibration, the rest is holdout")
    parser.add_argument("--z-hub-degree", type=int, default=None,
                        help="AA term only: forwarded to shared_neighbor_experiment.py's score_all "
                             "to zero out a shared neighbour's contribution once its own degree "
                             "exceeds this. Off (None) by default for backward compatibility.")
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

    if args.calibrate:
        result = run_calibration(
            db_path, args.co_commit_db, args.co_commit_vault, dates,
            args.sample, args.seed, args.split_frac, args.z_hub_degree,
        )
        print(json.dumps(result, indent=1))
        return

    result = run_experiment(
        vault_dir, db_path, args.co_commit_db, args.co_commit_vault, dates,
        args.sample, args.seed, args.rrf_k, args.tau * 24, args.combine,
        args.lam_recency, args.lam_cocommit, args.lam_aa, args.z_hub_degree,
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

    # mrr_at_lambdas with every lambda at 0 must reproduce the plain vector
    # baseline exactly - the calibration grid's "no boost" corner.
    pairs = [
        # target is index 2, currently ranked 2nd (index 1's 0.5 beats it,
        # index 0 excluded as the anchor) - a boost strong enough to pass 0.5
        # must move it to rank 1.
        {"anchor_index": 0, "target_index": 2, "baseline_rank": 2,
         "vector_scores": np.array([1.0, 0.5, 0.4, 0.1]),
         "recency_prox": np.array([0.0, 0.0, 1.0, 0.0]),
         "cc_prox": np.array([0.0, 0.0, 1.0, 0.0]),
         "aa_prox": np.array([0.0, 0.0, 0.0, 0.0])},
    ]
    index_of = {"a": 0, "b": 1, "c": 2, "d": 3}
    assert mrr_at_lambdas(pairs, index_of) == 1 / 2
    # a big enough recency+cocommit boost on the target (index 2) must move it
    # to rank 1 - the mechanism the grid search is choosing lambdas over.
    assert mrr_at_lambdas(pairs, index_of, lam_recency=0.5, lam_cocommit=0.5) == 1.0

    # grid_search must never let a stack's winner beat what an exhaustive scan
    # of the same grid finds - it would be a real bug in best_over's sort, not
    # a modeling question.
    winners = grid_search(pairs, index_of)
    exhaustive_best = max(
        mrr_at_lambdas(pairs, index_of, lam_recency=r, lam_cocommit=c)
        for r in LAM_RECENCY_GRID for c in LAM_COCOMMIT_GRID
    )
    assert winners["stack3_recency_cocommit"]["calib_mrr"] == round(exhaustive_best, 4)

    # z_hub_degree must reach score_all's AA term through build_pair_signals -
    # a note whose only shared neighbour is a hub gets aa_prox zeroed once the
    # cutoff engages, same fixture shape shared_neighbor_experiment.py's own
    # self-check uses (a~c share only z, degree 3).
    edges = [("a", "z"), ("b", "z"), ("c", "z"), ("a", "y"), ("b", "y")]
    neighbors = build_neighbor_sets(edges)
    fake_paths = ["a", "b", "c", "y", "z"]
    fake_index_of = {p: i for i, p in enumerate(fake_paths)}
    fake_pooled = np.eye(5)
    fake_usable = [("a", "c")]
    signals_no_cutoff = build_pair_signals(
        fake_usable, fake_paths, fake_index_of, fake_pooled, {}, {}, neighbors)
    signals_cutoff = build_pair_signals(
        fake_usable, fake_paths, fake_index_of, fake_pooled, {}, {}, neighbors, z_hub_degree=2)
    assert signals_no_cutoff[0]["aa_prox"][fake_index_of["c"]] > 0, \
        "sanity: a~c's only shared neighbour (z, degree 3) scores positive with no cutoff"
    assert signals_cutoff[0]["aa_prox"][fake_index_of["c"]] == 0.0, \
        "z_hub_degree=2 must reach build_pair_signals' AA term and zero out a~c (z has degree 3 > 2)"
    print("self-check ok")


if __name__ == "__main__":
    main()
