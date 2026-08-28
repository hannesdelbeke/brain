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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from co_retrieval import QUERY_LOG, read_new

WINDOW_S = 600  # two queries this close, in one vault, are one search
NEAR = 0.6  # SequenceMatcher ratio at which a rephrase is the same question
NARROW = 4  # fewer distinct notes than this is a narrow answer


def load(log_path: Path) -> list[dict]:
    """Every complete, parseable row, sorted by vault then time."""
    rows = []
    for line in read_new(Path(log_path), 0)[0]:
        try:
            row = json.loads(line)
            row["when"] = datetime.fromisoformat(row["t"])
            row["notes"] = sorted(set(row.get("results") or []))
            rows.append(row)
        except (ValueError, KeyError, TypeError):
            continue  # a foreign or half-written line is not worth failing a run over
    rows.sort(key=lambda row: (row["vault"], row["when"]))
    return rows


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
    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", type=Path, default=QUERY_LOG, help="searchd's query log")
    parser.add_argument("--vault", default="", help="only this vault")
    parser.add_argument("--window", type=int, default=WINDOW_S, help="reformulation window, seconds")
    parser.add_argument("--narrow", type=int, default=NARROW, help="distinct notes under this is narrow")
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()

    if args.selfcheck:
        return selfcheck()

    rows = [row for row in load(args.log) if not args.vault or row["vault"] == args.vault]
    if not rows:
        print(f"no queries in {args.log}. run some searches through searchd.py and come back.")
        return
    # rows come back sorted by vault, so the span is a min and a max, not the ends
    print(f"{len(rows)} queries, {min(r['t'] for r in rows)[:10]} to "
          f"{max(r['t'] for r in rows)[:10]}, {len(set(r['q'] for r in rows))} distinct")

    for label, hits in (
        ("empty", [r for r in rows if not r["notes"]]),
        ("narrow", [r for r in rows if r["notes"] and len(r["notes"]) < args.narrow]),
    ):
        print(f"\n{label}: {len(hits)}")
        for row in hits:
            print(f"  {row['t']}  [{row['vault']}] {len(row['notes'])} notes  {row['q']}")

    repeated = [run for run in runs(rows, args.window) if len(run) > 1]
    print(f"\nreformulated: {len(repeated)} runs over {sum(len(r) for r in repeated)} queries")
    for run in sorted(repeated, key=drift):
        span = (run[-1]["when"] - run[0]["when"]).total_seconds()
        print(f"  drift {drift(run):.2f}  {len(run)}x in {span:.0f}s  [{run[0]['vault']}] "
              f"{run[0]['q']}" + (f"  ->  {run[-1]['q']}" if run[-1]["q"] != run[0]["q"] else ""))


if __name__ == "__main__":
    main()
