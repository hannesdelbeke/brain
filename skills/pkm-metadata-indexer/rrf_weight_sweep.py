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
        rows.append(row)
    return {"grid": rows, "depth": depth, "queries": len(collected)}


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
        best = max(result["grid"], key=lambda row: row[f"ndcg@{args.depth}"])
        base = next(row for row in result["grid"] if row["w_vec"] == 1.0) \
            if any(row["w_vec"] == 1.0 for row in result["grid"]) else None
        print()
        print(f"best nDCG@{args.depth} at w_vec={best['w_vec']}:1 "
              f"({best[f'ndcg@{args.depth}']:.4f})")
        if base is not None:
            delta = best[f"ndcg@{args.depth}"] - base[f"ndcg@{args.depth}"]
            print(f"against the shipped 1:1 ({base[f'ndcg@{args.depth}']:.4f}), "
                  f"a change of {delta:+.4f}")
            print("one corpus and one label set. Hold it to a held-out split before "
                  "moving PKM_RRF_W_VEC.")
    else:
        print()
        print("sensitivity only, no labels given. Read it as: if the top-5 barely "
              "moves across the grid,\nthe weight is not worth a judged pass on this "
              "corpus. If it moves, the shipped 1:1 is\ncarrying real weight that "
              "nobody has ever measured.")

    if args.json:
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
