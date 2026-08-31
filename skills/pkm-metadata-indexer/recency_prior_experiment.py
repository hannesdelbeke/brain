"""Test the recency-proximity prior against real wikilinks, not an LLM judge.

The idea (see the "everything is connected" research note): fold time-closeness
into reranking as a multiplier, not a stored edge:

    final_score = vector_score * (1 + LAMBDA * exp(-|gap_days| / TAU))

No local LLM gateway was available to blind-judge relatedness the way
eval_related.py does, so this uses a ground truth that is already in the
vault and does not need a judge: an explicit [[wikilink]] between two notes is
a human saying, at write time, "these are related." For every note with at
least one resolved outbound link, this measures where the vector-only ranking
placed the linked target, and where the reranked-with-recency ranking placed
it, and reports whether the prior moved real, human-confirmed pairs up or
down.

    python skills/pkm-metadata-indexer/recency_prior_experiment.py --vault-dir <vault> --build-cache
    python skills/pkm-metadata-indexer/recency_prior_experiment.py --vault-dir <vault> --tau 30 --lam 0.5

Creation dates come from git history (first commit that added the path,
oldest-to-newest single walk, not one `git log` per file) and are cached to
`--cache` since building it is the slow part and every (tau, lambda)
configuration needs the same dates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm

DEFAULT_CACHE = Path.home() / ".pkm" / "recency-experiment-dates.json"


def build_creation_dates(vault_dir: Path) -> dict[str, str]:
    """Earliest commit date that added each current path, one git log walk.

    `--diff-filter=A --name-status --reverse` yields add events oldest-first
    across the whole history in a single pass; the first time a path appears
    in that stream is its creation date, which a per-file `git log` call
    (correct, but O(files) subprocesses) does not need to be.
    """
    proc = subprocess.run(
        ["git", "-C", str(vault_dir), "log", "--diff-filter=A", "--name-status",
         "--reverse", "--format=commit %ad", "--date=short"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    dates: dict[str, str] = {}
    current_date = None
    for line in proc.stdout.splitlines():
        if line.startswith("commit "):
            current_date = line[len("commit "):].strip()
        elif line.startswith("A\t"):
            path = line[2:].strip().replace("\\", "/")
            if path.endswith(".md") and path not in dates:
                dates[path] = current_date
    return dates


def gap_days(a: str, b: str) -> float:
    ya, ma, da = (int(part) for part in a.split("-"))
    yb, mb, db = (int(part) for part in b.split("-"))
    return abs((date(ya, ma, da) - date(yb, mb, db)).days)


def recency_proximity(a: str, b: str, tau: float) -> float:
    return float(np.exp(-gap_days(a, b) / tau))


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
                   tau: float, lam: float, sample: int, seed: int) -> dict:
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

    baseline_ranks, reranked_ranks = [], []
    for source, target in usable:
        anchor_index, target_index = index_of[source], index_of[target]
        vector_scores = pooled @ pooled[anchor_index]
        baseline_rank = rank_of(vector_scores, index_of, anchor_index, target_index)
        if baseline_rank is None:
            continue
        proximity = np.array([
            recency_proximity(dates[source], dates.get(path, dates[source]), tau)
            if path in dates else 0.0
            for path in paths
        ])
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
    return {
        "tau": tau, "lambda": lam, "pairs": n,
        "improved": improved, "worsened": worsened, "unchanged": n - improved - worsened,
        "mean_rank_baseline": round(float(np.mean(baseline_ranks)), 2),
        "mean_rank_reranked": round(float(np.mean(reranked_ranks)), 2),
        "mrr_baseline": round(mrr_baseline, 4),
        "mrr_reranked": round(mrr_reranked, 4),
        "mrr_change_pct": round((mrr_reranked / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--build-cache", action="store_true", help="(re)build the creation-date cache and exit")
    parser.add_argument("--tau", type=float, default=30.0, help="decay half-life-ish constant, in days")
    parser.add_argument("--lam", type=float, default=0.5, help="weight of the recency term")
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
    result = run_experiment(vault_dir, db_path, dates, args.tau, args.lam, args.sample, args.seed)
    print(json.dumps(result, indent=1))


def self_check():
    assert gap_days("2026-01-01", "2026-01-02") == 1
    assert gap_days("2026-01-10", "2026-01-01") == 9
    assert recency_proximity("2026-01-01", "2026-01-01", 30) == 1.0
    assert 0 < recency_proximity("2026-01-01", "2026-02-01", 30) < 1.0
    scores = np.array([0.9, 0.5, 0.99, 0.1])
    assert rank_of(scores, {}, exclude=2, target_index=0) == 1  # excluding the top score, 0 is now first
    print("self-check ok")


if __name__ == "__main__":
    main()
