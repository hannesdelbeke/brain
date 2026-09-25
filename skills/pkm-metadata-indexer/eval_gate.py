"""Judge the semantic gate: is a multi-facet query better off without the embedding?

`dual_track.SEMANTIC_GATE_FACETS` drops the semantic track when a query parses to
two or more facets. That decision was made on a 12-query latency-and-coverage
proxy and never put in front of a judge, which made it the least-evidenced choice
in the search path. This puts it in front of two.

The two arms are the live route, not a reimplementation of it:

    gated    GET /outline?q=...            the gate fires, structural + graph only
    semantic GET /outline?q=...&semantic=1  the gate is overridden, all three tracks

So the fusion, the weights and the embedding are production's, and the only
variable is whether track 1 ran. Two calls rather than one re-fused run, because
the arms differ in which tracks execute and no single run produces both.

Questions where the gate does not fire are excluded from the numbers, not averaged
into them. On a one-facet query both arms are the same call and score identically,
and a question set with enough of those reports "no difference" -- which reads as
"the gate is harmless" when it actually means "the gate was never tested".

The judge sees a note's title and the headings it contains, read from the index,
and never which arm found it or at what rank. Read from the index and not from the
arm's own payload on purpose: the payload carries only the headings the *facets*
matched, so a note the embedding alone found comes with an empty heading list, and
a judge shown less text about it says NO more often. That penalises the track
rather than the ranking, and it would have looked exactly like evidence for the
gate.

    python eval_gate.py --vault brain --port 44771 \
      --judge claude-sonnet-5 --judge claude-opus-5 \
      --questions eval_questions/outline-multifacet.json

Reports precision at k and mean first-useful rank per arm per judge, the latency
each arm cost, inter-judge agreement, and per-judge coverage.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

import dual_track
from eval_judge import (JUDGE_PROMPT, cache_key, compute_metrics, judge_all,
                        load_cache, load_questions, report_agreement, report_arms,
                        report_coverage, save_cache)

JUDGEMENTS = Path.home() / ".pkm" / "gate-judgements.json"
MAX_HEADINGS = 25  # A digest, not the note. Enough to decide, cheap to judge.
ARMS = ("gated", "semantic")


def outline(base: str, vault: str, question: str, limit: int,
            semantic: bool) -> tuple[list[str], dict]:
    """One arm: the ranked paths the route returned, and what it cost.

    `semantic=1` is the published override that exists so this comparison can be
    made at all -- see do_outline. Without it the route is production.
    """
    params = {"vault": vault, "q": question, "limit": limit}
    if semantic:
        params["semantic"] = "1"
    with urllib.request.urlopen(f"{base}/outline?" + urlencode(params), timeout=180) as response:
        body = json.load(response)
    ranked = [row["path"] for row in body["results"][vault]]
    return ranked, {
        "took_ms": body["took_ms"],
        "facet_count": body["facet_count"][vault],
        "semantic_skipped": body["semantic_skipped"][vault],
    }


def gate_fired(meta: dict[str, dict]) -> bool:
    """Did this question actually test the gate?

    Both halves have to hold. The gated arm must have skipped the track, and the
    override must have brought it back -- otherwise the two arms are the same call,
    they score identically, and averaging them in reports "no difference" where the
    truth is "not tested".
    """
    return meta["gated"]["semantic_skipped"] and not meta["semantic"]["semantic_skipped"]


def note_digest(connection: sqlite3.Connection, path: str) -> str:
    """Title and headings for one note, from the index rather than from an arm.

    Deduplicated: a long section is stored as several chunks under one heading, so
    the raw rows repeat it and a judge would be shown the same line four times.
    """
    rows = connection.execute(
        "SELECT heading, start_line FROM sections WHERE path = ? ORDER BY start_line",
        (path,)).fetchall()
    headings, seen = [], set()
    for heading, start_line in rows:
        if heading not in seen:
            seen.add(heading)
            headings.append(f"  L{start_line}: {heading}")
    lines = [f"Note: {path}"] + headings[:MAX_HEADINGS]
    if len(headings) > MAX_HEADINGS:
        lines.append(f"  ... ({len(headings) - MAX_HEADINGS} more sections)")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", default="brain")
    parser.add_argument("--port", type=int, default=44771)
    parser.add_argument("--limit", type=int, default=20, help="Route limit (DEFAULT_LIMIT)")
    parser.add_argument("--questions", default=None)
    parser.add_argument("--judge", action="append", dest="judges")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.questions or not args.judges:
        print("ERROR: need --questions and at least one --judge", file=sys.stderr)
        return 1

    base = f"http://127.0.0.1:{args.port}"
    with urllib.request.urlopen(f"{base}/health", timeout=30) as response:
        health = json.load(response)
    db_path = next((v["db"] for v in health["vaults"] if v["name"] == args.vault), None)
    if not db_path:
        print(f"ERROR: vault {args.vault!r} not served by the daemon", file=sys.stderr)
        return 1

    cached = load_cache(JUDGEMENTS)
    failures = {model: 0 for model in args.judges}
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    results, skipped = [], []

    for question, group in load_questions(args.questions):
        print(f"[{group}] {question}", flush=True)
        ranked = {}
        meta = {}
        for arm in ARMS:
            ranked[arm], meta[arm] = outline(base, args.vault, question, args.limit,
                                             semantic=(arm == "semantic"))

        if not gate_fired(meta):
            print(f"  gate did not fire (facets={meta['gated']['facet_count']}) -- excluded",
                  flush=True)
            skipped.append(question)
            continue

        all_notes = sorted(set(ranked["gated"][:10] + ranked["semantic"][:10]))
        digests = {path: note_digest(connection, path) for path in all_notes}
        pending = [(question, path, model,
                    JUDGE_PROMPT.format(question=question, content=digests[path]))
                   for path in all_notes for model in args.judges
                   if cache_key(question, path, model) not in cached]
        judge_all(pending, cached, failures)
        if pending:
            save_cache(JUDGEMENTS, cached)

        result = {
            "question": question,
            "group": group,
            "facet_count": meta["gated"]["facet_count"],
            # Per question, because the agreement pass needs *this* question's
            # notes; reading a loop variable after the loop compares the last
            # question's paths against every question's keys.
            "notes": all_notes,
            "took_ms": {arm: meta[arm]["took_ms"] for arm in ARMS},
            "judges": {},
        }
        for model in args.judges:
            verdicts = {path: cached.get(cache_key(question, path, model))
                        for path in all_notes}
            result["judges"][model] = {arm: compute_metrics(ranked[arm], verdicts)
                                       for arm in ARMS}
        results.append(result)

        for model in args.judges:
            for arm in ARMS:
                m = result["judges"][model][arm]
                print(f"  {model} {arm}: p@5={m['p5'][0]}/{m['p5'][1]} "
                      f"p@10={m['p10'][0]}/{m['p10'][1]} first={m['first_rank']}", flush=True)

    print("\n=== AGGREGATE RESULTS ===\n", flush=True)
    if not results:
        print("No question fired the gate. Nothing here is evidence about it.", flush=True)
        return 1
    print(f"Questions where the gate fired: {len(results)}"
          f"   excluded (one facet, arms identical): {len(skipped)}\n", flush=True)

    for model in args.judges:
        print(f"Judge: {model}", flush=True)
        report_arms(results, model, ARMS)
        report_coverage(results, cached, model, failures)
        print()

    report_agreement(results, cached, args.judges)

    # The other half of the decision. The gate was justified on cost, so cost is
    # reported next to quality rather than left in a docstring.
    for arm in ARMS:
        times = [r["took_ms"][arm] for r in results]
        print(f"Latency {arm}: mean {sum(times)/len(times):.0f} ms  "
              f"min {min(times):.0f}  max {max(times):.0f}", flush=True)
    print(f"\nSEMANTIC_GATE_FACETS is {dual_track.SEMANTIC_GATE_FACETS}; "
          f"GRAPH_RRF_WEIGHT is {dual_track.GRAPH_RRF_WEIGHT}.", flush=True)
    return 0


def self_check() -> int:
    import eval_judge
    eval_judge.self_check()

    # A heading repeated across chunks is shown once. The index stores one row per
    # chunk, so the raw rows repeat and an undeduped digest shows the same line
    # four times and spends the judge's attention on it.
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE sections (path TEXT, heading TEXT, start_line INT)")
    connection.executemany("INSERT INTO sections VALUES (?, ?, ?)", [
        ("n.md", "intro", 1), ("n.md", "intro", 1), ("n.md", "body", 9),
        ("other.md", "elsewhere", 1)])
    digest = note_digest(connection, "n.md")
    assert digest.count("intro") == 1, digest
    assert "L9: body" in digest, digest
    assert "elsewhere" not in digest, digest
    assert digest.splitlines()[0] == "Note: n.md", digest

    # A note with no sections still yields a judgeable line rather than an empty
    # string, so it is judged rather than silently treated as unanswerable.
    assert note_digest(connection, "missing.md") == "Note: missing.md"

    # The exclusion rule, asserted through the function main() calls. Writing the
    # condition out again here would pass even if main() had it backwards.
    def meta(gated: bool, semantic: bool) -> dict:
        return {"gated": {"semantic_skipped": gated},
                "semantic": {"semantic_skipped": semantic}}
    assert gate_fired(meta(True, False))          # gate fired, override worked
    assert not gate_fired(meta(False, False))     # one facet: never gated
    assert not gate_fired(meta(True, True))       # override did not take effect
    assert not gate_fired(meta(False, True))      # incoherent; counts as untested

    print("self-check ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
