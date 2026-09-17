"""Sweep the lexical/semantic fusion weight and report what it actually changes.

WHY. `/search` fuses two rankings, BM25 over sections_fts and cosine over the
section vectors, with Reciprocal Rank Fusion at an unweighted 1:1. Nobody chose
that ratio. It is what you get when you add two reciprocals together and it has
never been measured on this corpus.

The recency pass is the reason to care. Across every fusion function it tried,
the WEIGHT dominated the functional form: a 22.4-point swing from the weight
against 1.5 points from the timescale. Its sharpest case was RRF itself, where
an unweighted 1:1 scored -6.69%, worse than not fusing at all, and re-weighting
the same function to 9:1 recovered it monotonically to +5.02%. That measurement
fused content against recency, which is a different pair of lists from the one
here, so its 9:1 does not transfer and this script does not assume it does. What
transfers is the question: is 1:1 defensible, or is it just the number nobody
picked?

TWO MODES, AND THE CHEAP ONE COMES FIRST.

  SENSITIVITY (default, offline, no API cost). Before paying a judge to find the
  best weight, find out whether the weight moves anything at all. For each point
  on the grid this reports how far the ranking travels from the 1:1 baseline:
  how often rank 1 changes, how much of the top 5 survives, and how far the
  baseline's top 5 is displaced. If the top 5 barely moves, the knob is not
  worth tuning on this corpus and no judged pass should be bought. If it moves a
  lot, the ordering is resting on an arbitrary constant and the judged pass is
  the next thing to do.

  SCORED (`--labels`). Given relevance labels, report MRR and nDCG@5 per weight
  and name the best one. The labels file is JSON mapping a query string to the
  note paths that answer it:

      {"how do i back up my vault": ["sync/backup.md", "setup.md"]}

  There is deliberately no wikilink-derived ground truth here. The 2026-09-17
  measurement put wikilink labels at 1.97x [1.48, 2.55] optimistic, and a
  fusion weight chosen against an inflated label set is a weight chosen against
  the label set's bias.

COST. Retrieval and query encoding happen ONCE per query, then every grid point
re-fuses the same two candidate lists. A 40-point grid costs what 1 point costs.
That is the whole reason `retrieve_candidates` and `fuse_candidates` are
separate functions in index_pkm_meta.py.

USAGE

    python rrf_weight_sweep.py --vault-dir /path/to/vault
    python rrf_weight_sweep.py --vault-dir /path/to/vault --grid 0.25,0.5,1,2,4
    python rrf_weight_sweep.py --vault-dir /path/to/vault --labels labels.json
    python rrf_weight_sweep.py --vault-dir /path/to/vault --json out.json

Queries default to the real ones in ~/.pkm/queries.jsonl, deduplicated. Real
queries beat invented ones: they carry the actual mix of short lookups and long
natural-language questions, and that mix is exactly what a lexical/semantic
weight trades between.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import index_pkm_meta as pkm
import ranking_config

DEFAULT_QUERY_LOG = Path.home() / ".pkm" / "queries.jsonl"
DEFAULT_GRID = "0.111,0.25,0.5,0.667,1.0,1.5,2.0,4.0,9.0"


# ---------------------------------------------------------------------------
# queries
# ---------------------------------------------------------------------------

def load_queries_from_log(path: Path, vault: str | None = None) -> list[str]:
    """Distinct `/search` queries from the daemon's query log, oldest first.

    Deduplicated with an OrderedDict rather than a set so a rerun sweeps the
    same queries in the same order and two runs stay comparable.
    """
    seen: OrderedDict[str, None] = OrderedDict()
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("kind") != "search":
            continue
        if vault and row.get("vault") != vault:
            continue
        query = (row.get("q") or "").strip()
        if query:
            seen[query] = None
    return list(seen)


def load_queries_from_file(path: Path) -> list[str]:
    """Queries from a JSON file: a list of strings, or eval_questions' [q, split] pairs."""
    data = json.loads(path.read_text(encoding="utf-8"))
    queries = []
    for item in data:
        if isinstance(item, str):
            queries.append(item)
        elif isinstance(item, (list, tuple)) and item:
            queries.append(str(item[0]))
    return queries


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------

def note_order(ranked: list[dict], depth: int) -> list[str]:
    """The ranking collapsed from sections to notes, first occurrence wins.

    A reader gets notes, not sections, and two sections of one note filling the
    top two slots is one result to them. Every metric here is computed over
    notes for that reason.
    """
    seen: OrderedDict[str, None] = OrderedDict()
    for row in ranked:
        seen.setdefault(row["path"], None)
        if len(seen) >= depth:
            break
    return list(seen)


def jaccard(a: list[str], b: list[str]) -> float:
    left, right = set(a), set(b)
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def displacement(baseline: list[str], candidate: list[str], missing_penalty: int) -> float:
    """Mean move of each baseline item, with a fixed penalty for falling out.

    An item that leaves the measured window has moved at least to its edge, so
    it is charged `missing_penalty` rather than dropped, which would otherwise
    make a weight that ejects everything look perfectly stable.
    """
    if not baseline:
        return 0.0
    positions = {path: index for index, path in enumerate(candidate)}
    total = 0.0
    for index, path in enumerate(baseline):
        moved = abs(positions.get(path, missing_penalty) - index)
        total += moved
    return total / len(baseline)


def reciprocal_rank(order: list[str], relevant: set[str]) -> float:
    for index, path in enumerate(order, 1):
        if path in relevant:
            return 1.0 / index
    return 0.0


def ndcg_at(order: list[str], relevant: set[str], depth: int) -> float:
    """Binary-gain nDCG, which is all a path-level label set supports."""
    if not relevant:
        return 0.0
    gain = sum(
        1.0 / math.log2(index + 1)
        for index, path in enumerate(order[:depth], 1)
        if path in relevant
    )
    ideal = sum(
        1.0 / math.log2(index + 1)
        for index in range(1, min(len(relevant), depth) + 1)
    )
    return gain / ideal if ideal else 0.0


# ---------------------------------------------------------------------------
# sweep
# ---------------------------------------------------------------------------

def collect_candidates(queries: list[str], db_path: Path) -> list[dict]:
    """Retrieve both candidate lists once per query. This is the expensive part."""
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=60.0)
    try:
        cursor = connection.cursor()
        vectors = pkm.load_vectors(cursor)
        if vectors[1] is None:
            print("warning: the index holds no vectors, so only the lexical list exists "
                  "and no fusion weight can change anything.", file=sys.stderr)
        collected = []
        for position, query in enumerate(queries, 1):
            lexical, semantic = pkm.retrieve_candidates(cursor, query, vectors)
            collected.append({"query": query, "lexical": lexical, "semantic": semantic})
            if position % 25 == 0:
                print(f"  retrieved {position}/{len(queries)}", file=sys.stderr)
        return collected
    finally:
        connection.close()


def sweep(
    collected: list[dict],
    grid: list[float],
    depth: int,
    labels: dict[str, set[str]] | None,
) -> dict:
    """Re-fuse every query at every grid point and compare against the 1:1 baseline."""
    baselines = {
        item["query"]: note_order(
            pkm.fuse_candidates(item["lexical"], item["semantic"], w_lex=1.0, w_vec=1.0),
            depth,
        )
        for item in collected
    }

    # Fixed once, so every grid point is scored over the same queries in the
    # same order and the per-query series below line up for a paired test.
    scored_order = [item["query"] for item in collected
                    if labels is not None and labels.get(item["query"])]

    rows = []
    for w_vec in grid:
        top1_changed = 0
        overlaps = []
        moves = []
        rrs = []
        ndcgs = []
        for item in collected:
            order = note_order(
                pkm.fuse_candidates(item["lexical"], item["semantic"], w_lex=1.0, w_vec=w_vec),
                depth,
            )
            base = baselines[item["query"]]
            if (order[:1] or [None]) != (base[:1] or [None]):
                top1_changed += 1
            overlaps.append(jaccard(base[:depth], order[:depth]))
            moves.append(displacement(base[:depth], order[:depth], missing_penalty=depth))
            if labels is not None:
                relevant = labels.get(item["query"])
                if relevant:
                    rrs.append(reciprocal_rank(order, relevant))
                    ndcgs.append(ndcg_at(order, relevant, depth))
        row = {
            "w_vec": w_vec,
            "w_lex": 1.0,
            "top1_changed": top1_changed / len(collected) if collected else 0.0,
            f"top{depth}_jaccard": sum(overlaps) / len(overlaps) if overlaps else 1.0,
            "mean_displacement": sum(moves) / len(moves) if moves else 0.0,
        }
        if labels is not None:
            row["scored_queries"] = len(rrs)
            row["mrr"] = sum(rrs) / len(rrs) if rrs else 0.0
            row[f"ndcg@{depth}"] = sum(ndcgs) / len(ndcgs) if ndcgs else 0.0
            # Kept per query, not just averaged, because the question the table
            # cannot answer is whether a gap of a few thousandths is a result or
            # a coin landing the same way twice.
            row["rr_by_query"] = rrs
            row["ndcg_by_query"] = ndcgs
        rows.append(row)
    return {"grid": rows, "depth": depth, "queries": len(collected),
            "scored_order": scored_order}


# ---------------------------------------------------------------------------
# is the gap real
# ---------------------------------------------------------------------------

def paired_bootstrap(
    base: list[float],
    candidate: list[float],
    rounds: int = 10000,
    seed: int = 0,
) -> dict:
    """Mean per-query delta and a 95% interval, resampling queries with replacement.

    Paired, because both weights are scored on the same queries: the thing that
    varies between them is the ranking, and differencing per query removes the
    much larger variation between one query and the next. An interval that
    straddles zero means this corpus cannot tell the two weights apart — which
    is a finding, not a failure to find one.
    """
    diffs = [after - before for before, after in zip(base, candidate)]
    count = len(diffs)
    if not count:
        return {"delta": 0.0, "low": 0.0, "high": 0.0, "wins": 0, "losses": 0, "n": 0}
    rng = random.Random(seed)
    means = []
    for _ in range(rounds):
        means.append(sum(diffs[rng.randrange(count)] for _ in range(count)) / count)
    means.sort()
    return {
        "delta": sum(diffs) / count,
        "low": means[int(0.025 * rounds)],
        "high": means[min(int(0.975 * rounds), rounds - 1)],
        "wins": sum(1 for value in diffs if value > 0),
        "losses": sum(1 for value in diffs if value < 0),
        "n": count,
    }


def split_queries(queries: list[str], seed: int = 0) -> tuple[set[int], set[int]]:
    """A repeatable half-and-half split, by position under a fixed shuffle.

    Repeatable so that picking a weight and then checking it are not two
    different experiments, and by shuffle rather than by hash so the two halves
    are the same size on any corpus.
    """
    order = list(range(len(queries)))
    random.Random(seed).shuffle(order)
    half = len(order) // 2
    return set(order[:half]), set(order[half:])


def held_out(result: dict, metric: str, train: set[int], test: set[int]) -> dict:
    """Pick the best weight on one half, then report what it scores on the other.

    The grid has nine points and the corpus has tens of queries, so the best
    cell of a nine-cell table is partly a draw. This is the cheapest guard
    against reporting that draw as a tuning result.
    """
    def mean(row: dict, indices: set[int]) -> float:
        values = [value for index, value in enumerate(row[metric]) if index in indices]
        return sum(values) / len(values) if values else 0.0

    rows = result["grid"]
    baseline = next((row for row in rows if row["w_vec"] == 1.0), None)
    picked = max(rows, key=lambda row: mean(row, train))
    report = {
        "metric": metric,
        "picked_w_vec": picked["w_vec"],
        "train": mean(picked, train),
        "test": mean(picked, test),
    }
    if baseline is not None:
        report["baseline_train"] = mean(baseline, train)
        report["baseline_test"] = mean(baseline, test)
        report["test_delta"] = report["test"] - report["baseline_test"]
        report["bootstrap"] = paired_bootstrap(
            [value for index, value in enumerate(baseline[metric]) if index in test],
            [value for index, value in enumerate(picked[metric]) if index in test],
        )
    return report


# ---------------------------------------------------------------------------
# does the measurement have power, and is the effect one shape or many
# ---------------------------------------------------------------------------

ABLATIONS = (((1.0, 0.0), "lexical only"), ((0.0, 1.0), "vector only"))

LENGTH_BINS = ("1-2 words", "3-5 words", "6-9 words", "10+ words")


def scored_series(
    collected: list[dict],
    order: list[str],
    depth: int,
    labels: dict[str, set[str]],
    w_lex: float = 1.0,
    w_vec: float = 1.0,
) -> tuple[list[float], list[float]]:
    """Per-query RR and nDCG at one weight, emitted in `order` so pairs line up."""
    by_query = {item["query"]: item for item in collected}
    rrs, ndcgs = [], []
    for query in order:
        item = by_query[query]
        ranked = note_order(
            pkm.fuse_candidates(item["lexical"], item["semantic"],
                                w_lex=w_lex, w_vec=w_vec),
            depth,
        )
        relevant = labels[query]
        rrs.append(reciprocal_rank(ranked, relevant))
        ndcgs.append(ndcg_at(ranked, relevant, depth))
    return rrs, ndcgs


def power_check(
    collected: list[dict],
    order: list[str],
    depth: int,
    labels: dict[str, set[str]],
) -> list[dict]:
    """Can this corpus detect a difference that is certainly there?

    A null result only means something if the instrument could have said
    otherwise. So before believing that no weight beats 1:1, delete a whole
    retriever and check the metric notices. Dropping the vector list entirely
    is a far larger change than any point on the weight grid; a metric that
    cannot see it at this many queries could never have seen a weight tweak,
    and its flat sweep is a statement about the metric, not about the weight.

    Run per metric, because they do not have the same power. MRR looks at one
    rank per query and is nearly binary, so it throws away most of what
    separates two rankings; nDCG@k reads the whole top k.
    """
    base_rr, base_ndcg = scored_series(collected, order, depth, labels)
    checks = []
    for (w_lex, w_vec), name in ABLATIONS:
        rr, ndcg = scored_series(collected, order, depth, labels,
                                 w_lex=w_lex, w_vec=w_vec)
        checks.append({
            "ablation": name,
            "w_lex": w_lex,
            "w_vec": w_vec,
            "mrr": paired_bootstrap(base_rr, rr),
            "ndcg": paired_bootstrap(base_ndcg, ndcg),
        })
    return checks


def shuffled_null(
    collected: list[dict],
    order: list[str],
    depth: int,
    labels: dict[str, set[str]],
    w_vec: float,
    rounds: int = 5,
) -> dict:
    """The same test, against labels that have been detached from their queries.

    Permuting the label sets across queries destroys any real relevance while
    leaving every other property of the harness intact — same rankings, same
    label sizes, same bootstrap. A significant result here is impossible to
    earn honestly, so one means the pipeline has an artifact: an off-by-one in
    the pairing, a metric that rewards list length, a leak from ranking into
    labels. Zero across the rounds is the licence to read the real table.
    """
    label_sets = [labels[query] for query in order]
    trials = []
    for seed in range(rounds):
        shuffled = list(label_sets)
        random.Random(seed).shuffle(shuffled)
        fake = dict(zip(order, shuffled))
        base_rr, _ = scored_series(collected, order, depth, fake)
        cand_rr, _ = scored_series(collected, order, depth, fake, w_vec=w_vec)
        test = paired_bootstrap(base_rr, cand_rr)
        test["seed"] = seed
        test["significant"] = not (test["low"] <= 0.0 <= test["high"])
        trials.append(test)
    return {
        "w_vec": w_vec,
        "rounds": rounds,
        "false_positives": sum(1 for trial in trials if trial["significant"]),
        "trials": trials,
    }


def length_bin(query: str) -> str:
    """Which length bucket a query falls in — the feature the weight trades on.

    A lexical/semantic weight is supposed to matter differently for a two-word
    lookup than for a sentence, so query length is the first place to look for
    an effect that the average hides.
    """
    words = len(query.split())
    if words <= 2:
        return LENGTH_BINS[0]
    if words <= 5:
        return LENGTH_BINS[1]
    if words <= 9:
        return LENGTH_BINS[2]
    return LENGTH_BINS[3]


def binned_delta(
    collected: list[dict],
    order: list[str],
    grid: list[float],
    depth: int,
    labels: dict[str, set[str]],
) -> list[dict]:
    """Mean delta against 1:1 within each length bucket, rather than over all.

    An average of zero has two very different explanations: the weight does
    nothing anywhere, or it helps one kind of query and hurts another and the
    two cancel. Those call for opposite decisions — leave it alone, or make it
    depend on the query — and only the split table tells them apart. A gain
    that appears in exactly one bucket and nowhere else is an impulse, and
    with a handful of queries in that bucket it is usually noise wearing a
    pattern.
    """
    buckets: dict[str, list[int]] = {}
    for index, query in enumerate(order):
        buckets.setdefault(length_bin(query), []).append(index)

    base_rr, _ = scored_series(collected, order, depth, labels)
    deltas: dict[float, list[float]] = {}
    for w_vec in grid:
        if w_vec == 1.0:
            continue
        rr, _ = scored_series(collected, order, depth, labels, w_vec=w_vec)
        deltas[w_vec] = [after - before for before, after in zip(base_rr, rr)]

    return [
        {
            "bin": name,
            "n": len(buckets[name]),
            "delta": {w_vec: sum(values[i] for i in buckets[name]) / len(buckets[name])
                      for w_vec, values in deltas.items()},
        }
        for name in LENGTH_BINS if name in buckets
    ]


def contention(collected: list[dict], depth: int) -> dict:
    """How much room the weight has to work with, before any sweeping.

    A query whose candidates all came from one retriever cannot be reordered by
    any weight: the other list contributes nothing to every candidate alike. The
    fraction of queries where BOTH lists are non-empty, and the fraction of
    top-`depth` candidates that only one retriever found, bound what the whole
    sweep below can possibly show.
    """
    both = 0
    disputed = []
    for item in collected:
        lexical, semantic = item["lexical"], item["semantic"]
        if lexical and semantic:
            both += 1
        ranked = pkm.fuse_candidates(lexical, semantic, w_lex=1.0, w_vec=1.0)[:depth]
        if ranked:
            single = sum(
                1 for row in ranked
                if row["lex_rank"] is None or row["vec_rank"] is None
            )
            disputed.append(single / len(ranked))
    return {
        "both_retrievers_returned": both / len(collected) if collected else 0.0,
        f"top{depth}_found_by_one_retriever_only":
            sum(disputed) / len(disputed) if disputed else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sweep the lexical/semantic RRF weight and report what it changes.",
    )
    parser.add_argument("--vault-dir", type=Path, default=None,
                        help="vault root, defaults to the discovered one")
    parser.add_argument("--db", type=Path, default=None,
                        help="index database, defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--queries", type=Path, default=None,
                        help="JSON file of queries; defaults to ~/.pkm/queries.jsonl")
    parser.add_argument("--query-vault", default=None,
                        help="when reading the query log, keep only this vault's queries")
    parser.add_argument("--limit-queries", type=int, default=0,
                        help="cap the number of queries, 0 for all")
    parser.add_argument("--grid", default=DEFAULT_GRID,
                        help=f"comma-separated w_vec values against w_lex=1.0 (default {DEFAULT_GRID})")
    parser.add_argument("--depth", type=int, default=5,
                        help="how many notes deep to measure (default 5)")
    parser.add_argument("--labels", type=Path, default=None,
                        help="JSON of query -> [relevant note paths]; enables MRR and nDCG")
    parser.add_argument("--preflight", action=argparse.BooleanOptionalAction, default=True,
                        help="with labels, also run the power check, the shuffled null "
                             "and the per-length breakdown. On by default: they cost no "
                             "judgements and they decide whether the table above is readable")
    parser.add_argument("--json", type=Path, default=None,
                        help="write the full result, with the config snapshot, here")
    args = parser.parse_args()

    vault_dir = args.vault_dir.resolve() if args.vault_dir else pkm.find_vault_root()
    db_path = args.db.resolve() if args.db else pkm.default_db_path(vault_dir)
    if not db_path.exists():
        print(f"index database not found at {db_path}", file=sys.stderr)
        return 1

    if args.queries:
        queries = load_queries_from_file(args.queries)
        source = str(args.queries)
    else:
        queries = load_queries_from_log(DEFAULT_QUERY_LOG, args.query_vault)
        source = str(DEFAULT_QUERY_LOG)
    if args.limit_queries:
        queries = queries[: args.limit_queries]
    if not queries:
        print(f"no queries found in {source}", file=sys.stderr)
        return 1

    labels = None
    if args.labels:
        raw = json.loads(args.labels.read_text(encoding="utf-8"))
        labels = {query: set(paths) for query, paths in raw.items()}

    grid = [float(value) for value in args.grid.split(",") if value.strip()]

    print(f"vault    {vault_dir}")
    print(f"index    {db_path}")
    print(f"queries  {len(queries)} from {source}")
    print(f"grid     w_vec in {grid} against w_lex=1.0")
    print()

    collected = collect_candidates(queries, db_path)
    room = contention(collected, args.depth)
    result = sweep(collected, grid, args.depth, labels)
    result["contention"] = room
    result["config"] = ranking_config.snapshot()
    result["query_source"] = source

    print("HOW MUCH ROOM THE WEIGHT HAS")
    print(f"  both retrievers returned something   {room['both_retrievers_returned']:.1%} of queries")
    key = f"top{args.depth}_found_by_one_retriever_only"
    print(f"  top-{args.depth} entries only one retriever found  {room[key]:.1%}")
    print()

    header = f"{'w_vec:w_lex':>12}  {'top1 changed':>13}  {'top5 kept':>10}  {'mean move':>10}"
    if labels is not None:
        header += f"  {'MRR':>7}  {'nDCG@' + str(args.depth):>8}  {'n':>4}"
    print(header)
    print("-" * len(header))
    for row in result["grid"]:
        line = (
            f"{row['w_vec']:>9.3f}:1  "
            f"{row['top1_changed']:>12.1%}  "
            f"{row[f'top{args.depth}_jaccard']:>9.1%}  "
            f"{row['mean_displacement']:>10.2f}"
        )
        if labels is not None:
            line += (
                f"  {row['mrr']:>7.4f}  {row[f'ndcg@{args.depth}']:>8.4f}"
                f"  {row['scored_queries']:>4d}"
            )
        print(line)

    if labels is not None:
        print()
        print("IS ANY OF THAT REAL")
        print("  Every weight scored against the shipped 1:1 on the same queries,")
        print("  95% interval from 10000 paired resamples. An interval containing")
        print("  zero means this corpus cannot separate that weight from 1:1.")
        print()
        base = next((row for row in result["grid"] if row["w_vec"] == 1.0), None)
        if base is None:
            print("  no 1:1 point in the grid, so there is nothing to compare against")
        else:
            sub = f"{'w_vec:w_lex':>12}  {'d MRR':>8}  {'95% interval':>18}  {'won':>4}  {'lost':>5}"
            print(sub)
            print("  " + "-" * (len(sub) - 2))
            for row in result["grid"]:
                if row["w_vec"] == 1.0:
                    continue
                test = paired_bootstrap(base["rr_by_query"], row["rr_by_query"])
                verdict = "" if test["low"] <= 0.0 <= test["high"] else "  *"
                print(f"{row['w_vec']:>9.3f}:1  {test['delta']:>+8.4f}  "
                      f"[{test['low']:>+7.4f},{test['high']:>+7.4f}]  "
                      f"{test['wins']:>4d}  {test['losses']:>5d}{verdict}")
            print()
            print("  * marks an interval clear of zero. Nothing else on this table")
            print("    is evidence for moving the weight.")

        order = result["scored_order"]
        if len(order) >= 8 and base is not None:
            train, test_set = split_queries(order)
            print()
            print("HELD OUT")
            print(f"  {len(train)} queries to pick the weight, {len(test_set)} to check it.")
            for metric in ("rr_by_query", "ndcg_by_query"):
                report = held_out(result, metric, train, test_set)
                name = "MRR" if metric == "rr_by_query" else f"nDCG@{args.depth}"
                boot = report["bootstrap"]
                clear = "clear of zero" if not (boot["low"] <= 0.0 <= boot["high"]) \
                    else "contains zero"
                print(f"  {name:>8}: picked w_vec={report['picked_w_vec']}:1 on train "
                      f"({report['train']:.4f} vs 1:1 {report['baseline_train']:.4f})")
                print(f"  {'':>8}  on held-out it scores {report['test']:.4f} vs 1:1 "
                      f"{report['baseline_test']:.4f}, {report['test_delta']:+.4f} "
                      f"[{boot['low']:+.4f},{boot['high']:+.4f}] {clear}")
            result["held_out"] = {
                metric: held_out(result, metric, train, test_set)
                for metric in ("rr_by_query", "ndcg_by_query")
            }

        if args.preflight and order and base is not None:
            checks = power_check(collected, order, args.depth, labels)
            result["power_check"] = checks
            print()
            print("DOES THIS MEASUREMENT HAVE POWER")
            print("  Each metric against a whole retriever removed — a change far")
            print("  bigger than anything on the grid. A metric that misses this")
            print("  cannot be read as evidence that the weight does nothing.")
            print()
            for check in checks:
                for name, test in (("MRR", check["mrr"]),
                                   (f"nDCG@{args.depth}", check["ndcg"])):
                    seen = "detects" if not (test["low"] <= 0.0 <= test["high"]) \
                        else "MISSES "
                    print(f"  {check['ablation']:>13}  {name:>8}  {seen}  "
                          f"{test['delta']:>+8.4f}  "
                          f"[{test['low']:>+7.4f},{test['high']:>+7.4f}]")
            blind = sorted({name for check in checks
                            for name, test in (("MRR", check["mrr"]),
                                               (f"nDCG@{args.depth}", check["ndcg"]))
                            if test["low"] <= 0.0 <= test["high"]})
            if blind:
                print()
                print(f"  {', '.join(blind)} cannot see an ablation. Read the sweep on")
                print("  the other metric, or judge more queries.")

            apparent = max((row for row in result["grid"] if row["w_vec"] != 1.0),
                           key=lambda row: row["mrr"])
            null = shuffled_null(collected, order, args.depth, labels,
                                 apparent["w_vec"])
            result["shuffled_null"] = null
            print()
            print("SHUFFLED NULL")
            print(f"  {apparent['w_vec']:g}:1 against 1:1, with the label sets permuted")
            print("  across queries so no real effect survives. Any significant round")
            print("  here is an artifact in the harness, not a result.")
            print(f"  {null['false_positives']}/{null['rounds']} rounds came back significant.")

            table = binned_delta(collected, order, grid, args.depth, labels)
            result["binned"] = table
            weights = [w for w in grid if w != 1.0]
            print()
            print("BINNED BY QUERY LENGTH")
            print("  d MRR against 1:1 inside each bucket. A number that appears in")
            print("  one row and nowhere else is an impulse, not a trend.")
            print()
            print(f"  {'bin':>10} {'n':>4} " + "".join(f"{w:>9.3f}:1" for w in weights))
            for entry in table:
                cells = "".join(f"{entry['delta'][w]:>+11.4f}" for w in weights)
                print(f"  {entry['bin']:>10} {entry['n']:>4} {cells}")
    else:
        print()
        print("sensitivity only, no labels given. Read it as: if the top-5 barely "
              "moves across the grid,\nthe weight is not worth a judged pass on this "
              "corpus. If it moves, the shipped 1:1 is\ncarrying real weight that "
              "nobody has ever measured.")

    if args.json:
        # The per-query series stay, since they are what a later reader would
        # need to re-test any of this. What someone searched for does not: it is
        # the one thing here that is about the person rather than the ranking,
        # and this file gets pasted into notes and issues.
        result.pop("scored_order", None)
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
