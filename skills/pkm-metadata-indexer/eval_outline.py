"""Judge the outline ranking change: old full-graph voting vs new filtered voting.

The dual-track fusion changed how the graph walk contributes to the final ranking:
- OLD: graph votes on all notes it returns, at weight 1.0
- NEW: graph votes only on notes the facet track did NOT find, at weight 0.5

This eval tests GRAPH FUSION ONLY. The semantic track is stubbed to return empty,
so both arms fuse the same structural+graph rankings with different graph weights.
It is silent on the semantic gate (facet_count >= 2) since that gate acts on a
track this eval does not run -- eval_gate.py judges that one, against the live
route, because a stubbed track cannot be evidence about whether to run it.

Both arms run from the same track outputs, so the only difference is graph fusion.
A judge that sees only the question and the outline content for one note decides if
that note is useful. The judge harness -- the request shape, the cache, the metrics
and the coverage report -- is eval_judge.py, shared rather than copied.

    python eval_outline.py --vault brain --port 44771 --judge claude-sonnet-5 --judge claude-opus-5 \
      --questions eval_questions/outline-multifacet.json

Reports precision at k, mean rank of first useful note, inter-judge agreement, and
per-judge coverage.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import dual_track
import eval_judge
from eval_judge import (cache_key, compute_metrics, judge_all, load_cache,
                        load_questions, report_agreement, report_arms,
                        report_coverage, save_cache)

JUDGEMENTS = Path.home() / ".pkm" / "outline-judgements.json"
RRF_K = 60  # Same constant as dual_track.py
ARMS = ("old", "new")

# Kept here verbatim rather than taken from eval_judge, because the cache on disk
# holds verdicts formed under this exact wording and this eval's content really is
# "the headings the search matched" -- eval_judge's phrasing describes a note's own
# headings. Rewording it would mix two framings in one cache for no gain.
JUDGE_PROMPT = """Someone searching their notes asks: "{question}"

Below is one note from the search results, shown as it would appear in the outline:
the note's title and the section headings the search matched.

---
{content}
---

Would this note help answer the question? Answer with one word, YES or NO."""


def search_tracks(db_path: str, question: str, limit: int = 50) -> dict:
    """Run both semantic and structural tracks once, returning raw track outputs.

    Calls dual_track_search directly to get the full payload including separate
    semantic, structural, and graph tracks that we'll re-fuse both ways.

    The semantic track runs via a stub that returns empty - we're testing the
    structural/graph fusion, and the semantic track would require loading models.
    For the NEW arm this doesn't matter (semantic is gated at facet_count >= 2),
    but the OLD arm needs *some* semantic list to fuse, so we pass an empty one.
    """
    # Stub semantic function that returns empty - the real daemon would call rank()
    def semantic_stub(query: str) -> list[dict]:
        return []

    return dual_track.dual_track_search(
        db_path, question,
        semantic=semantic_stub,
        hops=2, top=limit, facets=None,
        gate_semantic=True  # Let the gate work naturally
    )


def reciprocal_rank_fusion(rankings: list[list[str]], weights: list[float],
                          k: int = RRF_K) -> dict[str, float]:
    """Fuse ranked path lists. A path missing from a ranking contributes nothing."""
    scores: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights):
        for index, path in enumerate(ranking):
            scores[path] = scores.get(path, 0.0) + weight / (k + index + 1)
    return scores


def fuse_old(structural: list[str], graph: list[str]) -> list[str]:
    """OLD fusion: graph votes on all notes at weight 1.0."""
    fused = reciprocal_rank_fusion([structural, graph], [1.0, 1.0])
    return [path for path, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)]


def fuse_new(structural: list[str], graph: list[str]) -> list[str]:
    """NEW fusion: graph filtered to non-facet notes and weighted 0.5."""
    facet_set = set(structural)
    graph_filtered = [path for path in graph if path not in facet_set]
    fused = reciprocal_rank_fusion([structural, graph_filtered], [1.0, 0.5])
    return [path for path, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)]


def note_outline_content(payload: dict, path: str) -> str:
    """Build the outline snippet a judge will see for one note.

    This is what a caller would actually get: title + headings from the facet matches.
    The judge must NOT be told which arm produced it or at what rank.
    """
    lines = [f"Note: {path}"]

    # Check if title matched
    for row in payload.get("structural", []):
        if row["path"] == path and row.get("titled"):
            lines.append("  (title matched)")
            break

    # Add section headings
    for row in payload.get("structural", []):
        if row["path"] == path:
            for heading in row.get("headings", []):
                end = heading.get("end_line")
                if end and end > heading["line"]:
                    span = f"L{heading['line']}-{end}"
                elif not end:
                    span = f"L{heading['line']}+"
                else:
                    span = f"L{heading['line']}"
                lines.append(f"  {span}: {heading['heading']}")
            break

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=False,
                        help="Path to index database (required if not using --vault/--port)")
    parser.add_argument("--vault", default=None, help="Vault name for daemon health check")
    parser.add_argument("--port", type=int, default=44771, help="Daemon port for health check")
    parser.add_argument("--questions", default=None,
                        help="JSON list of [question, group] pairs")
    parser.add_argument("--judge", action="append", dest="judges",
                        help="Judge model (repeat for multiple judges)")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()

    if not args.questions:
        print("ERROR: Must specify --questions (unless running --self-check)", file=sys.stderr)
        return 1

    if not args.judges:
        print("ERROR: Must specify at least one --judge model", file=sys.stderr)
        return 1

    questions = load_questions(args.questions)

    # Get db path from --db or from daemon health check
    db_path = args.db
    if not db_path:
        if not args.vault:
            print("ERROR: Must specify either --db or --vault", file=sys.stderr)
            return 1
        base = f"http://127.0.0.1:{args.port}"
        with urllib.request.urlopen(f"{base}/health", timeout=30) as response:
            health = json.load(response)
        db_path = next((v["db"] for v in health["vaults"] if v["name"] == args.vault), None)
        if not db_path:
            print(f"ERROR: Vault '{args.vault}' not found in daemon", file=sys.stderr)
            return 1

    cached = load_cache(JUDGEMENTS)
    # Counted in memory, not in the cache: a failed call is deliberately never
    # cached, so the cache cannot be asked afterwards how many calls failed.
    failures = {model: 0 for model in args.judges}

    results = []  # One entry per question

    for question, group in questions:
        print(f"[{group}] {question}", flush=True)

        # Run search once
        payload = search_tracks(db_path, question)

        # Extract track outputs
        structural = [row["path"] for row in payload.get("structural", [])]
        graph = [row["path"] for row in payload.get("graph", [])]
        facet_count = payload.get("facet_count", 0)

        # Fuse both ways
        ranked = {"old": fuse_old(structural, graph),
                  "new": fuse_new(structural, graph)}

        all_notes = sorted(set(ranked["old"][:10] + ranked["new"][:10]))
        contents = {path: note_outline_content(payload, path) for path in all_notes}
        pending = [(question, path, model,
                    JUDGE_PROMPT.format(question=question, content=contents[path]))
                   for path in all_notes for model in args.judges
                   if cache_key(question, path, model) not in cached
                   and contents[path].strip()]
        judge_all(pending, cached, failures)
        if pending:
            save_cache(JUDGEMENTS, cached)

        result = {
            "question": question,
            "group": group,
            "facet_count": facet_count,
            # Kept per question because the agreement pass needs *this*
            # question's notes; reading a loop variable after the loop compares
            # the last question's paths against every question's keys.
            "notes": all_notes,
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
    for model in args.judges:
        print(f"Judge: {model}", flush=True)
        report_arms(results, model, ARMS)
        report_coverage(results, cached, model, failures)
        print()
    report_agreement(results, cached, args.judges)
    return 0


def self_check():
    """Verify the shared harness, then this eval's own fusion arms."""
    eval_judge.self_check()

    # Test 2: old arm with self-agreeing graph note
    # structural=[a, b], graph=[a, c]
    # In old fusion: 'a' gets 2 votes (structural rank 0, graph rank 0)
    # 'b' gets 1 vote (structural rank 1)
    # 'c' gets 1 vote (graph rank 1)
    # So 'a' ranks first due to double-counting
    old = fuse_old(["a", "b"], ["a", "c"])
    assert old[0] == "a", f"OLD arm should rank self-agreeing 'a' first, got {old}"

    # Test 3: new arm filters graph membership
    # Graph filtered: 'a' is in structural, so graph becomes just ["c"]
    # Votes: 'a' gets structural rank 0 = 1 full vote
    #        'b' gets structural rank 1 = 1 vote at lower rank
    #        'c' gets graph rank 0 at weight 0.5 = 0.5 vote
    # 'a' should still be first (best structural rank), but not double-counted
    new = fuse_new(["a", "b"], ["a", "c"])
    assert new[0] == "a", f"NEW arm should rank 'a' first (best structural), got {new}"

    # Test 4: precision math
    verdicts = {"a": True, "b": False, "c": None, "d": True}
    ranked = ["b", "c", "a", "d"]
    metrics = compute_metrics(ranked, verdicts)
    # Top 5: b(False), c(None), a(True), d(True) -> 2 useful out of 4
    assert metrics["p5"] == (2, 4), f"Expected (2, 4), got {metrics['p5']}"
    assert metrics["first_rank"] == 3, f"First useful is 'a' at rank 3, got {metrics['first_rank']}"

    print("self-check ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
