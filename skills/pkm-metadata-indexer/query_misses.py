"""Read searchd's query log and print what search did not find.

`searchd.py` logs every `/search` and `/similar` to `~/.pkm/queries.jsonl`. That
log is the only record of a search that went nowhere, and nothing reads it for
that. This does:

    python skills/pkm-metadata-indexer/query_misses.py
    python skills/pkm-metadata-indexer/query_misses.py --vault brain --window 600
    python skills/pkm-metadata-indexer/query_misses.py --selfcheck

Three signals, all derivable from the fields the log actually carries
(`t kind vault q limit took_ms results`, results being paths):

  empty        no results at all.
  narrow       the result set is a few notes repeated, one row per matching
               section. searchd fills the limit whatever the query, so the
               count of rows says nothing and the count of distinct notes is
               the only measure of how much was found.
  reformulated the same or a near-same query again in one vault inside a
               window. Asking twice is the searcher saying the first answer was
               wrong. `drift` is the overlap between the first and last result
               set of a run: 1.00 means the rephrase changed nothing, 0.00
               means search returned a different set of notes for what the
               searcher meant as the same question.

A fourth signal, a top score far under the corpus median, is not built: the log
stores result paths and no scores, on purpose, so the number does not exist to
read. It would need a writer change first.

A row carrying an `origin` in `NO_RESULT_DATA_ORIGINS` was reconstructed after the
fact, from a transcript that recorded the query and not the answer. Its `results` is
empty because nothing was captured, not because search found nothing, so it is left
out of `empty` and `narrow` and prints `--` for drift. It still counts for
reformulation, which needs only the query text and the clock. `--include-backfill`
puts it back in, which is what you want when auditing the backfill itself and not
when measuring search.

Read-only, and it reads the whole log from offset 0 every run rather than
resuming. It shares `read_new` with `co_retrieval.py` but not that module's
stored offset, which stays where co-retrieval left it.
"""

import argparse
import json
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from co_retrieval import QUERY_LOG, read_new, resolve_log_paths

WINDOW_S = 600  # two queries this close, in one vault, are one search
NEAR = 0.6  # SequenceMatcher ratio at which a rephrase is the same question
NARROW = 4  # fewer distinct notes than this is a narrow answer

# a row reconstructed after the fact records the query and not what came back, so its
# empty `results` means "unknown" rather than "found nothing". the signals built on
# result sets, empty and narrow and drift, have to skip it or every such row reads as a
# miss. the signals built on the query text and its timestamp, reformulation and
# frequency, are unaffected and keep it.
NO_RESULT_DATA_ORIGINS = {"backfill_claude_transcript"}


def has_result_data(row: dict) -> bool:
    """Whether this row's `results` is a real answer rather than a backfill placeholder."""
    return row.get("origin") not in NO_RESULT_DATA_ORIGINS


def load_all(log_paths: list[Path]) -> list[dict]:
    """Every complete, parseable row across all log paths, sorted by vault then time."""
    rows = []
    for log_path in log_paths:
        p = Path(log_path)
        if not p.exists():
            continue
        for line in read_new(p, 0)[0]:
            try:
                row = json.loads(line)
                row["when"] = datetime.fromisoformat(row["t"])
                row["notes"] = sorted(set(row.get("results") or []))
                rows.append(row)
            except (ValueError, KeyError, TypeError):
                continue  # a foreign or half-written line is not worth failing a run over
    rows.sort(key=lambda row: (row["vault"], row["when"]))
    return rows


def load(log_path: Path) -> list[dict]:
    """Every complete, parseable row, sorted by vault then time. Retained for backwards compatibility."""
    return load_all([Path(log_path)])


def runs(rows: list[dict], window_s: int = WINDOW_S) -> list[list[dict]]:
    """Group near-same queries in one vault inside the window.

    Any open run, not just the last one: two questions asked alternately are two
    reformulations interleaved, and chaining only to the previous row sees four
    unrelated queries instead.
    """
    # ponytail: rescans every open run per row, so O(n^2) over the log. Bound the
    # scan by time if the log ever gets long enough to notice.
    grouped: list[list[dict]] = []
    for row in rows:
        for run in reversed(grouped):
            last = run[-1]
            if (last["vault"] == row["vault"]
                    and 0 <= (row["when"] - last["when"]).total_seconds() <= window_s
                    and SequenceMatcher(None, last["q"].lower(), row["q"].lower()).ratio() >= NEAR):
                run.append(row)
                break
        else:
            grouped.append([row])
    return grouped


def drift(run: list[dict]) -> float:
    """Jaccard of the first and last result set of a run. 1.0 is no change."""
    first, last = set(run[0]["notes"]), set(run[-1]["notes"])
    return 1.0 if not (first or last) else len(first & last) / len(first | last)


def selfcheck():
    def row(t, q, notes=(), vault="v"):
        return {"t": t, "vault": vault, "q": q, "when": datetime.fromisoformat(t),
                "notes": sorted(set(notes))}

    assert drift([row("2026-01-01T00:00:00", "a", [])]) == 1.0, "two empty sets have not drifted"
    one = row("2026-01-01T00:00:00", "a", ["x.md"])
    assert drift([one, row("2026-01-01T00:00:10", "a", ["y.md"])]) == 0.0, "no shared note is full drift"
    assert drift([one, one]) == 1.0, "the same set twice has not drifted"
    assert drift([one, row("2026-01-01T00:00:10", "a", ["x.md", "y.md"])]) == 0.5, "half shared is half"

    near = [row("2026-01-01T00:00:00", "how to water a fern"),
            row("2026-01-01T00:00:30", "how do you water the fern")]
    assert len(runs(near)) == 1, "a rephrase inside the window is one run"
    assert len(runs(near, window_s=10)) == 2, "and two runs once the window closes"
    assert len(runs([near[0], row("2026-01-01T00:00:30", "sourdough starter")])) == 2, \
        "an unrelated query is its own run"
    assert len(runs([near[0], row("2026-01-01T00:00:30", "how to water a fern", vault="w")])) == 2, \
        "the same query in another vault is not a reformulation"
    interleaved = [near[0], row("2026-01-01T00:00:10", "sourdough starter"),
                   near[1], row("2026-01-01T00:00:40", "sourdough starter")]
    assert [len(run) for run in runs(interleaved)] == [2, 2], \
        "two questions asked alternately are two runs, not four lone queries"

    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        log = Path(temp) / "queries.jsonl"
        assert load(log) == [], "no log yet is not an error, it is no rows"
        with log.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps({"t": "2026-01-01T00:00:01", "kind": "search", "vault": "b",
                                     "q": "x", "limit": 5, "results": ["a.md", "a.md"]}) + "\n")
            handle.write("not json\n")
            handle.write('{"t": "2026-01-01T00:00:02", "vault": "b", "resul')
        rows = load(log)
        assert len(rows) == 1, f"one good row, a bad line and a half line, got {len(rows)}"
        assert rows[0]["notes"] == ["a.md"], "one note in two sections is one note found"

        log2 = Path(temp) / "queries_device2.jsonl"
        with log2.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps({"t": "2026-01-01T00:00:03", "kind": "search", "vault": "b",
                                     "q": "y", "limit": 5, "results": ["c.md"]}) + "\n")
        all_rows = load_all([log, log2])
        assert len(all_rows) == 2, f"expected 2 rows from 2 files, got {len(all_rows)}"
        assert all_rows[0]["q"] == "x" and all_rows[1]["q"] == "y"
    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", type=Path, default=None,
                        help="searchd's query log (default: vault telemetry or ~/.pkm/queries.jsonl)")
    parser.add_argument("--vault", default="", help="only this vault")
    parser.add_argument("--window", type=int, default=WINDOW_S, help="reformulation window, seconds")
    parser.add_argument("--narrow", type=int, default=NARROW, help="distinct notes under this is narrow")
    parser.add_argument("--include-backfill", action="store_true",
                        help="count backfilled rows as empty results, which they are not, "
                             f"origins treated as having no result data: {sorted(NO_RESULT_DATA_ORIGINS)}")
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()

    if args.selfcheck:
        return selfcheck()

    log_paths = resolve_log_paths(args.vault, args.log)
    rows = [row for row in load_all(log_paths) if not args.vault or row["vault"] == args.vault]
    if not rows:
        source_desc = str(log_paths[0]) if len(log_paths) == 1 else f"{len(log_paths)} log files"
        print(f"no queries in {source_desc}. run some searches through searchd.py and come back.")
        return
    # rows come back sorted by vault, so the span is a min and a max, not the ends
    print(f"{len(rows)} queries, {min(r['t'] for r in rows)[:10]} to "
          f"{max(r['t'] for r in rows)[:10]}, {len(set(r['q'] for r in rows))} distinct")

    scored = rows if args.include_backfill else [r for r in rows if has_result_data(r)]
    skipped = len(rows) - len(scored)
    if skipped:
        print(f"{skipped} backfilled rows carry no result data and are excluded from empty and "
              f"narrow, pass --include-backfill to count them")

    for label, hits in (
        ("empty", [r for r in scored if not r["notes"]]),
        ("narrow", [r for r in scored if r["notes"] and len(r["notes"]) < args.narrow]),
    ):
        print(f"\n{label}: {len(hits)}")
        for row in hits:
            print(f"  {row['t']}  [{row['vault']}] {len(row['notes'])} notes  {row['q']}")

    # reformulation is read off the query text and the clock, so a backfilled run is as
    # real as a live one and stays in. drift is read off the result sets, so it is
    # unknowable for a run with no result data and prints as -- rather than as a
    # confident 1.00 meaning the rephrase changed nothing.
    repeated = [run for run in runs(rows, args.window) if len(run) > 1]
    print(f"\nreformulated: {len(repeated)} runs over {sum(len(r) for r in repeated)} queries")
    for run in sorted(repeated, key=drift):
        span = (run[-1]["when"] - run[0]["when"]).total_seconds()
        scorable = all(has_result_data(r) for r in run)
        shown = f"{drift(run):.2f}" if scorable else "  --"
        print(f"  drift {shown}  {len(run)}x in {span:.0f}s  [{run[0]['vault']}] "
              f"{run[0]['q']}" + (f"  ->  {run[-1]['q']}" if run[-1]["q"] != run[0]["q"] else ""))


if __name__ == "__main__":
    main()
