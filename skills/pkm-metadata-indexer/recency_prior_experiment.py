"""Test the recency-proximity prior against real wikilinks, not an LLM judge.

The idea (see the "everything is connected" research note): fold time-closeness
into ranking. Three ways to combine it with the vector score, in increasing
order of how well they avoid displacing an already-good candidate:

    mul (rejected): final = vector_score * (1 + LAMBDA * proximity)
    add (promising): final = vector_score + LAMBDA * proximity
    rrf (untested):  final = 1/(k+vector_rank) + 1/(k+recency_rank)

and two shapes for `proximity` under mul/add (ignored for rrf, which ranks by
raw gap directly):

    decay: proximity = exp(-gap_hours / TAU)
    hard:  proximity = 1.0 if gap_hours <= TAU else 0.0

`mul` with `decay` or `hard` was tested first (tau in days: 3-1000, hours:
1-720, lambda: 0.05-10) and rejected — see the research note. The failure mode
found was not the target's own score dropping at long range (already ~0 there
either way); it was OTHER candidates close in time to the anchor getting
boosted past a genuinely-linked but older target, an UNBOUNDED displacement:
a rival's score can jump by an arbitrary multiple. `add` bounds the maximum
displacement to LAMBDA regardless of proximity, which a quick check showed
gets `improved > worsened` for the first time. `rrf`, per a 2025 paper (Re3,
arXiv 2509.01306) and how production hybrid search actually combines
relevance and freshness, fuses by RANK POSITION instead of rescaling a score,
capping a signal's contribution at 1/k no matter how many temporal rivals
exist — structurally immune to the failure mode proven for `mul`.

No local LLM gateway was available to blind-judge relatedness the way
eval_related.py does, so this uses a ground truth that is already in the
vault and does not need a judge: an explicit [[wikilink]] between two notes is
a human saying, at write time, "these are related." For every note with at
least one resolved outbound link, this measures where the vector-only ranking
placed the linked target, and where the reranked-with-recency ranking placed
it, and reports whether the prior moved real, human-confirmed pairs up or
down.

    python skills/pkm-metadata-indexer/recency_prior_experiment.py --vault-dir <vault> --build-cache
    python skills/pkm-metadata-indexer/recency_prior_experiment.py --vault-dir <vault> --combine mul --mode decay --tau 30 --unit days --lam 0.5
    python skills/pkm-metadata-indexer/recency_prior_experiment.py --vault-dir <vault> --combine add --mode decay --tau 30 --unit days --lam 0.01
    python skills/pkm-metadata-indexer/recency_prior_experiment.py --vault-dir <vault> --combine rrf --tau 60

Creation timestamps (full ISO datetime, not just a date, so an hours-scale
cutoff is measurable) come from git history (first commit that added the
path, one oldest-to-newest walk rather than one `git log` per file) and are
cached to `--cache` since building it is the slow part and every
configuration needs the same timestamps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm

DEFAULT_CACHE = Path.home() / ".pkm" / "recency-experiment-datetimes.json"


def build_creation_dates(vault_dir: Path) -> dict[str, str]:
    """Earliest commit ISO timestamp that added each current path, one git log walk.

    `--diff-filter=A --name-status --reverse` yields add events oldest-first
    across the whole history in a single pass; the first time a path appears
    in that stream is its creation timestamp, which a per-file `git log` call
    (correct, but O(files) subprocesses) does not need to be. `%aI` is the
    strict ISO 8601 author date with timezone, precise to the second, which a
    plain `--date=short` (day only) cannot support an hours-scale cutoff with.
    """
    proc = subprocess.run(
        ["git", "-C", str(vault_dir), "log", "--diff-filter=A", "--name-status",
         "--reverse", "--format=commit %aI"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    dates: dict[str, str] = {}
    current = None
    for line in proc.stdout.splitlines():
        if line.startswith("commit "):
            current = line[len("commit "):].strip()
        elif line.startswith("A\t"):
            path = line[2:].strip().replace("\\", "/")
            if path.endswith(".md") and path not in dates:
                dates[path] = current
    return dates


def gap_hours(a: str, b: str) -> float:
    return abs((datetime.fromisoformat(a) - datetime.fromisoformat(b)).total_seconds()) / 3600.0


def recency_proximity(a: str, b: str, tau: float, mode: str = "decay") -> float:
    hours = gap_hours(a, b)
    if mode == "hard":
        return 1.0 if hours <= tau else 0.0
    return float(np.exp(-hours / tau))


def note_vectors(meta, matrix):
    """Mean-pool section vectors into one per note, renormalised. Same
    definition searchd.py's /graph and /duplicates routes use, so a note's
    position here means the same thing it would through those endpoints."""
    paths, index_of = [], {}
    for _, path, _, _ in meta:
        if path not in index_of:
            index_of[path] = len(paths)
            paths.append(path)
    rows = np.fromiter((index_of[row[1]] for row in meta), dtype=np.intp, count=len(meta))
    pooled = np.zeros((len(paths), matrix.shape[1]), dtype=np.float32)
    np.add.at(pooled, rows, matrix)
    pooled /= np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9)
    return paths, index_of, pooled


def wikilink_ground_truth(db_path: Path) -> list[tuple[str, str]]:
    import sqlite3
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return connection.execute(
            "SELECT DISTINCT source_path, resolved_target_path FROM edges "
            "WHERE resolved_target_path IS NOT NULL AND source_path != resolved_target_path"
        ).fetchall()
    finally:
        connection.close()


def rrf_fuse(vector_scores: np.ndarray, gaps_hours: np.ndarray, k: float = 60.0) -> np.ndarray:
    """Reciprocal rank fusion of a vector-similarity list and a recency list.

    The multiplicative and additive priors above rescale one candidate's raw
    score by how close it is in time to the anchor, which is unbounded: a
    candidate with proximity near 1 can jump an arbitrary distance regardless
    of how many other candidates are also close, which is the mechanism the
    research note proves causes damage that scales with rival count. RRF fuses
    by RANK POSITION instead (`1/(k+rank)` per list, summed) — a signal's
    contribution is capped at `1/k` no matter how skewed its distribution is
    or how many rivals share a similar rank, which is the structural reason
    production hybrid search systems combine relevance and recency this way
    rather than by rescaling one score with the other.
    """
    n = len(vector_scores)
    vector_rank = np.empty(n, dtype=np.float64)
    vector_rank[np.argsort(-vector_scores)] = np.arange(n)
    recency_rank = np.empty(n, dtype=np.float64)
    recency_rank[np.argsort(gaps_hours)] = np.arange(n)  # smaller gap = closer = better rank
    return 1.0 / (k + vector_rank) + 1.0 / (k + recency_rank)


def rank_of(scores: np.ndarray, index_of: dict, exclude: int, target_index: int) -> int | None:
    """1-based rank of target_index among all notes but `exclude` (the anchor itself)."""
    order = np.argsort(-scores)
    rank = 1
    for index in order:
        if index == exclude:
            continue
        if index == target_index:
            return rank
        rank += 1
    return None


def run_experiment(vault_dir: Path, db_path: Path, dates: dict[str, str],
                   tau_hours: float, lam: float, sample: int, seed: int,
                   mode: str = "decay", combine: str = "mul") -> dict:
    import sqlite3
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    paths, index_of, pooled = note_vectors(meta, matrix)

    links = wikilink_ground_truth(db_path)
    usable = [(a, b) for a, b in links
             if a in index_of and b in index_of and a in dates and b in dates]
    rng = np.random.default_rng(seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]

    baseline_ranks, reranked_ranks, boosted_candidate_counts = [], [], []
    for source, target in usable:
        anchor_index, target_index = index_of[source], index_of[target]
        vector_scores = pooled @ pooled[anchor_index]
        baseline_rank = rank_of(vector_scores, index_of, anchor_index, target_index)
        if baseline_rank is None:
            continue
        if combine == "rrf":
            # No proximity function needed: RRF ranks candidates by raw gap
            # directly. A missing creation date gets a sentinel gap larger than
            # any real one, so it always ranks last on the recency list rather
            # than contaminating a real candidate's position.
            gaps = np.array([
                gap_hours(dates[source], dates[path]) if path in dates else 1e9
                for path in paths
            ])
            reranked_scores = rrf_fuse(vector_scores, gaps, k=tau_hours)
        else:
            proximity = np.array([
                recency_proximity(dates[source], dates.get(path, dates[source]), tau_hours, mode)
                if path in dates else 0.0
                for path in paths
            ])
            if mode == "hard":
                boosted_candidate_counts.append(int((proximity > 0).sum()) - 1)  # exclude the anchor
            if combine == "add":
                # A brainstormed alternative to the rejected multiplier: an
                # additive term of size lam can only flip an order whose raw
                # vector-score gap is smaller than lam, so small lam is
                # structurally incapable of displacing a candidate that was
                # clearly better on content alone - unlike the multiplier, which
                # flips whenever proximity favours the rival at all, regardless
                # of the underlying score gap (see the rank-flip derivation in
                # the research note).
                reranked_scores = vector_scores + lam * proximity
            else:
                reranked_scores = vector_scores * (1 + lam * proximity)
        reranked_rank = rank_of(reranked_scores, index_of, anchor_index, target_index)
        baseline_ranks.append(baseline_rank)
        reranked_ranks.append(reranked_rank)

    n = len(baseline_ranks)
    if n == 0:
        return {"error": "no usable wikilinked pairs with known creation dates"}
    improved = sum(1 for b, r in zip(baseline_ranks, reranked_ranks) if r < b)
    worsened = sum(1 for b, r in zip(baseline_ranks, reranked_ranks) if r > b)
    mrr_baseline = float(np.mean([1 / r for r in baseline_ranks]))
    mrr_reranked = float(np.mean([1 / r for r in reranked_ranks]))
    result = {
        "mode": mode, "combine": combine,
        "rrf_k" if combine == "rrf" else "tau_hours": tau_hours,
        "lambda": None if combine == "rrf" else lam,
        "pairs": n,
        "improved": improved, "worsened": worsened, "unchanged": n - improved - worsened,
        "mean_rank_baseline": round(float(np.mean(baseline_ranks)), 2),
        "mean_rank_reranked": round(float(np.mean(reranked_ranks)), 2),
        "mrr_baseline": round(mrr_baseline, 4),
        "mrr_reranked": round(mrr_reranked, 4),
        "mrr_change_pct": round((mrr_reranked / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }
    if mode == "hard" and combine != "rrf":
        # How many candidates a typical anchor's boost even touches: the whole
        # point of a hard cutoff is fewer eligible candidates than the decay
        # tail had, so this number is the mechanism check, not a side note.
        result["mean_boosted_candidates"] = round(float(np.mean(boosted_candidate_counts)), 2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--build-cache", action="store_true", help="(re)build the creation-date cache and exit")
    parser.add_argument("--mode", choices=["decay", "hard"], default="decay",
                        help="shape of the proximity function, ignored when --combine rrf. "
                             "decay: smooth exponential tail. hard: step function, 1 within "
                             "--tau, 0 outside it")
    parser.add_argument("--combine", choices=["mul", "add", "rrf"], default="mul",
                        help="mul: vector_score*(1+lam*proximity), the original rejected form. "
                             "add: vector_score+lam*proximity, a tiebreaker that cannot flip a "
                             "clearly-better candidate. rrf: reciprocal-rank-fuse a vector-rank "
                             "list with a recency-rank list (--tau doubles as the RRF k constant, "
                             "--lam ignored) - structurally cannot displace an unbounded amount")
    parser.add_argument("--tau", type=float, default=30.0,
                        help="decay: the exponential time constant. hard: the cutoff. rrf: the "
                             "RRF k constant (--unit ignored for rrf). in --unit units otherwise")
    parser.add_argument("--unit", choices=["hours", "days"], default="days",
                        help="unit --tau is given in, converted to hours internally")
    parser.add_argument("--lam", type=float, default=0.5,
                        help="weight of the recency term, ignored when --combine rrf")
    parser.add_argument("--sample", type=int, default=400, help="wikilinked pairs to sample")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)

    if args.build_cache or not args.cache.exists():
        began = time.perf_counter()
        dates = build_creation_dates(vault_dir)
        args.cache.parent.mkdir(parents=True, exist_ok=True)
        args.cache.write_text(json.dumps(dates), encoding="utf-8")
        print(f"cached {len(dates)} creation dates in {time.perf_counter() - began:.1f}s -> {args.cache}",
              flush=True)
        if args.build_cache:
            return

    dates = json.loads(args.cache.read_text(encoding="utf-8"))
    tau_hours = args.tau if args.combine == "rrf" else (
        args.tau * 24 if args.unit == "days" else args.tau)
    result = run_experiment(vault_dir, db_path, dates, tau_hours, args.lam,
                            args.sample, args.seed, args.mode, args.combine)
    print(json.dumps(result, indent=1))


def self_check():
    assert gap_hours("2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00") == 24.0
    assert gap_hours("2026-01-01T06:00:00+00:00", "2026-01-01T00:00:00+00:00") == 6.0
    assert recency_proximity("2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00", 30) == 1.0
    assert 0 < recency_proximity("2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00", 30 * 24) < 1.0
    # hard mode: exactly at the cutoff counts as in range, past it does not
    assert recency_proximity("2026-01-01T00:00:00+00:00", "2026-01-01T06:00:00+00:00", 6, "hard") == 1.0
    assert recency_proximity("2026-01-01T00:00:00+00:00", "2026-01-01T06:00:01+00:00", 6, "hard") == 0.0
    scores = np.array([0.9, 0.5, 0.99, 0.1])
    assert rank_of(scores, {}, exclude=2, target_index=0) == 1  # excluding the top score, 0 is now first

    # rrf_fuse: candidate 0 is #2 by vector score but #1 by recency (smallest
    # gap), candidate 1 is #1 by vector but far in time -> fusion should not
    # simply reproduce either ranking alone
    vector_scores = np.array([0.5, 0.9, 0.1])
    gaps = np.array([1.0, 500.0, 2.0])
    fused = rrf_fuse(vector_scores, gaps, k=1.0)
    assert np.argmax(fused) == 0, "closest-in-time-and-second-by-vector should win a small-k fusion"
    # RRF fuses by rank position, not raw score, so rescaling vector_scores
    # (same relative order, different magnitude) must not change the outcome -
    # exactly the property that makes it immune to the "unbounded rescale"
    # failure mode proven for the multiplicative combine.
    rescaled = rrf_fuse(vector_scores * 1000, gaps, k=1.0)
    assert np.array_equal(np.argsort(-fused), np.argsort(-rescaled))
    print("self-check ok")


if __name__ == "__main__":
    main()
