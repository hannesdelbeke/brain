"""Build a relevance label set for the fusion weight sweep, using a blind judge.

`rrf_weight_sweep.py --labels` can say which weight ranks best, but only if
something has said which notes were the right answers. This writes that file.

The labels are pooled: for one query, every section that reaches the top of the
ranking at *any* point on the weight grid is judged, and nothing else is. That
bounds the cost to what the comparison can actually see — a note no weight can
surface cannot change which weight wins — and, more importantly, it keeps the
pool neutral. A pool built from one weight's output would hand that weight a
head start, because the rival weights would be scored against a label set
assembled from their opponent's hits.

Two things this deliberately is not:

  - It is not wikilink-derived. The links a note happens to carry were measured
    against judged relevance on this vault and ran 1.97x optimistic, so a sweep
    resting on them would report a gain that is mostly the proxy's error.
  - It is not a ranking the judge can see. The judge is shown one question and
    one section, never a rank, never a weight, never which list retrieved it.

Judgements are cached in ~/.pkm/rerank-judgements.json — the same file and the
same key that eval_rerank.py uses, so the two tools warm each other's cache and
a rerun costs nothing for pairs already seen.

    python build_labels.py --db <index.db> --query-vault <vault> --out ~/.pkm/rrf-labels.json
    python rrf_weight_sweep.py --db <index.db> --labels ~/.pkm/rrf-labels.json

Env: GATEWAY, MODEL — read by eval_rerank, which owns the judge. Point MODEL at
whatever the local gateway lists; the dialect follows the name.

The output holds real queries and real note paths, so it belongs outside any
repository. The default path is under ~/.pkm for that reason.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_rerank
import index_pkm_meta as pkm
import rrf_weight_sweep as sweep

DEFAULT_OUT = Path.home() / ".pkm" / "rrf-labels.json"


def section_key(row: dict) -> str:
    """The judgement-cache key, identical to the one eval_rerank writes."""
    return f"{row['path']}#{row['start_line']}"


def pool(item: dict, grid: list[float], depth: int, cap: int) -> list[dict]:
    """Every section any grid point ranks in its top `depth`, at most `cap` of them.

    Ordered by how early a section first appears, so that when the cap bites it
    drops the sections that only ever placed low — the ones least able to decide
    which weight wins.
    """
    first_seen: dict[str, tuple[int, dict]] = {}
    for w_vec in grid:
        ranked = pkm.fuse_candidates(item["lexical"], item["semantic"],
                                     w_lex=1.0, w_vec=w_vec)
        for rank, row in enumerate(ranked[:depth]):
            identity = section_key(row)
            if identity not in first_seen or rank < first_seen[identity][0]:
                first_seen[identity] = (rank, row)
    ordered = sorted(first_seen.values(), key=lambda pair: pair[0])
    return [row for _, row in ordered[:cap]]


def judge_pool(
    query: str,
    rows: list[dict],
    cursor: sqlite3.Cursor,
    cached: dict,
    withhold: bool,
    workers: int,
) -> tuple[dict[str, bool | None], int]:
    """Judge whatever is not already cached. Returns verdicts and a withheld count."""
    need = [row for row in rows if f"{query}|{section_key(row)}" not in cached]
    # sqlite is single threaded, so every read happens before the fan-out.
    texts = [eval_rerank.section_text(cursor, {"path": row["path"],
                                               "line": row["start_line"],
                                               "snippet": row.get("snippet")})
             for row in need]

    withheld = 0
    if withhold:
        flagged = [eval_rerank.private(text) for text in texts]
        withheld = sum(1 for names in flagged if names)
        for row, names in zip(need, flagged):
            if names:
                # Recorded as a judgement so a rerun does not retry it, and as
                # None rather than False so it reads as "not asked", not "no".
                cached[f"{query}|{section_key(row)}"] = None
        need = [row for row, names in zip(need, flagged) if not names]
        texts = [text for text, names in zip(texts, flagged) if not names]

    if need:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            verdicts = executor.map(lambda pair: eval_rerank.judge(*pair),
                                    [(query, text) for text in texts])
            for row, verdict in zip(need, verdicts):
                cached[f"{query}|{section_key(row)}"] = verdict

    return ({section_key(row): cached.get(f"{query}|{section_key(row)}")
             for row in rows}, withheld)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", required=True, type=Path, help="index database to read")
    parser.add_argument("--query-log", type=Path, default=sweep.DEFAULT_QUERY_LOG,
                        help="jsonl search log to take real queries from")
    parser.add_argument("--query-vault", default=None,
                        help="only queries logged against this vault")
    parser.add_argument("--queries", type=Path, default=None,
                        help="a file of queries, one per line, instead of the log")
    parser.add_argument("--max-queries", type=int, default=0,
                        help="stop after this many queries (0 = all)")
    parser.add_argument("--grid", default=sweep.DEFAULT_GRID,
                        help="the w_vec grid the pool must cover; must match the sweep's")
    parser.add_argument("--depth", type=int, default=5,
                        help="how deep into each grid point's ranking the pool reaches")
    parser.add_argument("--cap", type=int, default=15,
                        help="most sections judged per query")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--withhold-private", action=argparse.BooleanOptionalAction,
                        default=True,
                        help="keep sections matching the private patterns off the wire. "
                             "On by default here, unlike eval_rerank, because this runs "
                             "over whatever was really searched for, not a written list")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="where to write the labels")
    args = parser.parse_args()

    if args.queries:
        queries = sweep.load_queries_from_file(args.queries)
    else:
        queries = sweep.load_queries_from_log(args.query_log, args.query_vault)
    if args.max_queries:
        queries = queries[:args.max_queries]
    if not queries:
        print("no queries to label", file=sys.stderr)
        return 1

    grid = [float(value) for value in args.grid.split(",")]
    print(f"{len(queries)} queries, grid {grid}, depth {args.depth}, "
          f"model {eval_rerank.MODEL}", file=sys.stderr)

    collected = sweep.collect_candidates(queries, args.db)

    eval_rerank.JUDGEMENTS.parent.mkdir(parents=True, exist_ok=True)
    cached = (json.loads(eval_rerank.JUDGEMENTS.read_text(encoding="utf-8"))
              if eval_rerank.JUDGEMENTS.exists() else {})
    before = len(cached)

    connection = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True, timeout=60.0)
    labels: "OrderedDict[str, list[str]]" = OrderedDict()
    judged_sections = withheld_total = 0
    try:
        cursor = connection.cursor()
        for position, item in enumerate(collected, 1):
            rows = pool(item, grid, args.depth, args.cap)
            verdicts, withheld = judge_pool(item["query"], rows, cursor, cached,
                                            args.withhold_private, args.workers)
            judged_sections += len(rows)
            withheld_total += withheld
            # A note is relevant if any of its judged sections was useful.
            relevant = OrderedDict()
            for row in rows:
                if verdicts.get(section_key(row)):
                    relevant.setdefault(row["path"], None)
            labels[item["query"]] = list(relevant)
            eval_rerank.JUDGEMENTS.write_text(
                json.dumps(cached, indent=1, sort_keys=True), encoding="utf-8")
            if position % 10 == 0 or position == len(collected):
                print(f"  judged {position}/{len(collected)} queries", file=sys.stderr)
    finally:
        connection.close()

    with_labels = sum(1 for paths in labels.values() if paths)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(labels, indent=1), encoding="utf-8")

    print(f"\n{len(labels)} queries, {with_labels} with at least one relevant note "
          f"({with_labels / len(labels):.0%})", file=sys.stderr)
    print(f"{judged_sections} sections pooled, {len(cached) - before} newly judged, "
          f"{withheld_total} withheld as private", file=sys.stderr)
    print(f"mean relevant notes per labelled query: "
          f"{sum(len(p) for p in labels.values()) / max(with_labels, 1):.1f}",
          file=sys.stderr)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
