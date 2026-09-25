"""Judge the outline ranking change: old full-graph voting vs new filtered voting.

The dual-track fusion changed how the graph walk contributes to the final ranking:
- OLD: graph votes on all notes it returns, at weight 1.0
- NEW: graph votes only on notes the facet track did NOT find, at weight 0.5

This eval tests GRAPH FUSION ONLY. The semantic track is stubbed to return empty,
so both arms fuse the same structural+graph rankings with different graph weights.
It is silent on the semantic gate (facet_count >= 2) since that gate acts on a
track this eval does not run.

Both arms run from the same track outputs, so the only difference is graph fusion.
A judge that sees only the question and the outline content for one note decides if
that note is useful. Verdicts are cached by (question, note, judge_model), so two
judges never read each other's answers and a rerun is free. Failed judgements are
NOT cached and will be retried on the next run.

    python eval_outline.py --vault brain --port 44771 --judge claude-sonnet-5 --judge claude-opus-5 \
      --questions eval_questions/outline-multifacet.json

Reports precision at k, mean rank of first useful note, inter-judge agreement, and
per-judge abstention counts.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Import the shared judge infrastructure and dual_track functions
from eval_rerank import post, judge_answer, private, PRIVATE
import dual_track

GATEWAY = os.environ.get("GATEWAY", "http://127.0.0.1:8080")
JUDGEMENTS = Path.home() / ".pkm" / "outline-judgements.json"
RRF_K = 60  # Same constant as dual_track.py

JUDGE_PROMPT = """Someone searching their notes asks: "{question}"

Below is one note from the search results, shown as it would appear in the outline:
the note's title and the section headings the search matched.

---
{content}
---

Would this note help answer the question? Answer with one word, YES or NO."""


def cache_key(question: str, path: str, model: str) -> str:
    """The one place a judgement's identity is spelled.

    The judge model belongs in the key: two judges scoring the same (question,
    note) must not read each other's verdict, and a key that omits the model
    silently fuses them into one voter whose numbers look like agreement.
    """
    return f"{question}|{path}|{model}"


def agreement(results: list[dict], cached: dict, j1: str, j2: str) -> list[bool]:
    """Did the two judges say the same thing, over the pairs both actually saw.

    Per question, from that question's own note list. Counted only where both
    judges have a verdict -- a pair one judge never answered is not a
    disagreement, and folding it in would make a thin judge look contrary.
    """
    return [cached[cache_key(result["question"], path, j1)]
            == cached[cache_key(result["question"], path, j2)]
            for result in results for path in result["notes"]
            if cache_key(result["question"], path, j1) in cached
            and cache_key(result["question"], path, j2) in cached]


def judge_request(model: str, prompt: str) -> tuple[str, dict]:
    """URL and body for one judgement, in whichever dialect the model speaks.

    No `temperature`: the gateway rejects it outright for claude-opus-5 and
    claude-sonnet-5 with "temperature is deprecated for this model", and an
    HTTPError is a URLError, so sending it turns every judgement into a caught
    exception and a judge that answered nothing looks like one that rejected
    everything.

    `max_tokens` is 512 and not the 8 a one-word answer needs, because
    claude-opus-5 uses adaptive thinking and spends the budget before it writes
    anything: at 8 and at 64 tokens it returned finish_reason "length" and an
    empty string on 293 of 349 real prompts, at 256 it answered 79% of them and
    at 512 it answers all of them. A one-word verdict needs a paragraph of
    headroom. Sonnet does not engage thinking on this prompt and was unaffected,
    which is exactly why a single-judge eval hid this.
    """
    if model.startswith("gemini"):
        return f"{GATEWAY}/v1beta/models/{model}:generateContent", {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 8,
                                 "thinkingConfig": {"thinkingBudget": 0}},
        }
    return f"{GATEWAY}/v1/chat/completions", {
        "model": model, "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }


def load_questions(path: str) -> list[tuple[str, str]]:
    """Read a question set. Same shape as eval_rerank: [[question, group], ...]."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(row[0], row[1]) for row in rows]


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


def judge(question: str, content: str, model: str) -> bool | None:
    """Ask one judge model if this note is useful."""
    if not content.strip():
        return None

    url, payload = judge_request(
        model, JUDGE_PROMPT.format(question=question, content=content))
    try:
        data = post(url, payload, timeout=120)
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  judge {model} failed: {error}", flush=True)
        return None

    answer = judge_answer(model, data).strip().upper()
    if answer.startswith(("YES", "NO")):
        return answer.startswith("YES")
    # Said out loud rather than returned quietly. An unparseable reply and a
    # failed call both became None here, so a model that was burning its whole
    # token budget on thinking and returning "" was indistinguishable from one
    # that had judged the note unhelpful -- for two full runs.
    print(f"  judge {model} gave no verdict: {answer[:60]!r}"
          f" (finish {data.get('choices', [{}])[0].get('finish_reason')})", flush=True)
    return None


def precision_at_k(ranked: list[str], verdicts: dict[str, bool | None], k: int) -> tuple[int, int]:
    """Count useful notes in top k."""
    useful = sum(1 for path in ranked[:k] if verdicts.get(path))
    return useful, min(k, len(ranked))


def first_useful_rank(ranked: list[str], verdicts: dict[str, bool | None]) -> int | None:
    """1-indexed rank of first useful note, or None if none useful."""
    for rank, path in enumerate(ranked):
        if verdicts.get(path):
            return rank + 1
    return None


def compute_metrics(ranked: list[str], verdicts: dict[str, bool | None]) -> dict:
    """Compute all metrics for one arm."""
    p5_useful, p5_total = precision_at_k(ranked, verdicts, 5)
    p10_useful, p10_total = precision_at_k(ranked, verdicts, 10)
    first = first_useful_rank(ranked, verdicts)

    return {
        "p5": (p5_useful, p5_total),
        "p10": (p10_useful, p10_total),
        "first_rank": first,
        "has_useful": first is not None,
    }


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

    JUDGEMENTS.parent.mkdir(parents=True, exist_ok=True)
    cached = json.loads(JUDGEMENTS.read_text(encoding="utf-8")) if JUDGEMENTS.exists() else {}
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
        old_ranked = fuse_old(structural, graph)
        new_ranked = fuse_new(structural, graph)

        # Collect all notes we need to judge (top 10 from each arm)
        all_notes = set(old_ranked[:10] + new_ranked[:10])

        # Prepare judge inputs
        note_contents = {path: note_outline_content(payload, path) for path in all_notes}

        # Identify what needs judging (not cached)
        need_judging = []
        for path in all_notes:
            for model in args.judges:
                if cache_key(question, path, model) not in cached:
                    need_judging.append((question, path, model, note_contents[path]))

        # Judge in parallel
        if need_judging:
            with ThreadPoolExecutor(max_workers=8) as pool:
                jobs = [(q, content, model) for q, path, model, content in need_judging]
                for (q, path, model, content), verdict in zip(need_judging,
                        pool.map(lambda job: judge(*job), jobs)):
                    # A failure is retried next run, never remembered: a cached
                    # null is indistinguishable from "the judge said no", and
                    # scoring it as not-useful reads a broken call as a verdict.
                    if verdict is None:
                        failures[model] += 1
                    else:
                        cached[cache_key(q, path, model)] = verdict

            JUDGEMENTS.write_text(json.dumps(cached, indent=1, sort_keys=True), encoding="utf-8")

        # Build verdict dicts per judge
        per_judge = {}
        for model in args.judges:
            per_judge[model] = {
                path: cached.get(cache_key(question, path, model))
                for path in all_notes
            }

        # Compute metrics per judge per arm
        result = {
            "question": question,
            "group": group,
            "facet_count": facet_count,
            # Kept per question because the agreement pass needs *this*
            # question's notes; reading a loop variable after the loop compares
            # the last question's paths against every question's keys.
            "notes": sorted(all_notes),
            "judges": {},
        }

        for model in args.judges:
            verdicts = per_judge[model]
            result["judges"][model] = {
                "old": compute_metrics(old_ranked, verdicts),
                "new": compute_metrics(new_ranked, verdicts),
            }

        results.append(result)

        # Print per-question summary
        for model in args.judges:
            m = result["judges"][model]
            print(f"  {model}:", flush=True)
            print(f"    old: p@5={m['old']['p5'][0]}/{m['old']['p5'][1]} "
                  f"p@10={m['old']['p10'][0]}/{m['old']['p10'][1]} "
                  f"first={m['old']['first_rank']}", flush=True)
            print(f"    new: p@5={m['new']['p5'][0]}/{m['new']['p5'][1]} "
                  f"p@10={m['new']['p10'][0]}/{m['new']['p10'][1]} "
                  f"first={m['new']['first_rank']}", flush=True)

    # Aggregate reporting
    print("\n=== AGGREGATE RESULTS ===\n", flush=True)

    # Coverage, not abstention, is the number that catches an unusable judge.
    # A judge can be missing verdicts two ways: it was asked and failed, or the
    # run stopped before it was asked at all. The second is invisible in the
    # failure count, and it is the one that actually happened -- one judge
    # answered 332 pairs and the other 32, and both reported 0 failures.
    expected = {model: sum(len(r["notes"]) for r in results) for model in args.judges}
    judged = {model: sum(1 for r in results for path in r["notes"]
                         if cache_key(r["question"], path, model) in cached)
              for model in args.judges}

    for model in args.judges:
        print(f"Judge: {model}", flush=True)
        for arm in ("old", "new"):
            p5_useful = sum(r["judges"][model][arm]["p5"][0] for r in results)
            p5_total = sum(r["judges"][model][arm]["p5"][1] for r in results)
            p10_useful = sum(r["judges"][model][arm]["p10"][0] for r in results)
            p10_total = sum(r["judges"][model][arm]["p10"][1] for r in results)

            first_ranks = [r["judges"][model][arm]["first_rank"]
                          for r in results if r["judges"][model][arm]["first_rank"]]
            mean_first = sum(first_ranks) / len(first_ranks) if first_ranks else None
            answered = len(first_ranks)

            p5_pct = f"{p5_useful/p5_total:.1%}" if p5_total else "n/a"
            p10_pct = f"{p10_useful/p10_total:.1%}" if p10_total else "n/a"
            mean_str = f"{mean_first:.1f}" if mean_first else "none"

            print(f"  {arm}: precision@5 {p5_useful}/{p5_total} = {p5_pct}  "
                  f"precision@10 {p10_useful}/{p10_total} = {p10_pct}", flush=True)
            print(f"       answered {answered}/{len(results)}  "
                  f"mean first useful rank {mean_str}", flush=True)

        want, got = expected[model], judged[model]
        share = got / want if want else 0.0
        print(f"  coverage: {got}/{want} pairs judged = {share:.1%}"
              f"   calls that failed this run: {failures[model]}", flush=True)
        if share < 0.90:
            print(f"  WARNING: {model} judged only {share:.0%} of its pairs. Its numbers "
                  f"above are NOT comparable to a judge with full coverage -- an unjudged "
                  f"note scores the same as a rejected one.", flush=True)
        print()

    # Inter-judge agreement
    if len(args.judges) == 2:
        j1, j2 = args.judges
        agreements = agreement(results, cached, j1, j2)

        if agreements:
            agree_count = sum(agreements)
            total = len(agreements)
            print(f"Inter-judge agreement: {agree_count}/{total} = {agree_count/total:.1%}", flush=True)
            print(f"  ({j1} vs {j2} on {total} (question, note) pairs)", flush=True)

    return 0


def self_check():
    """Verify cache key includes judge model and test fusion logic."""
    # Test 1: the cache key must separate judges. Asserted through the function
    # the run actually calls -- a test that rebuilds the key with its own
    # f-string passes even when the caller's key has no model in it, which is
    # the bug this is here to catch.
    assert cache_key("q", "a.md", "judge-one") != cache_key("q", "a.md", "judge-two")
    assert cache_key("q", "a.md", "j") == cache_key("q", "a.md", "j")
    assert cache_key("q1", "a.md", "j") != cache_key("q2", "a.md", "j")
    assert cache_key("q", "a.md", "j") != cache_key("q", "b.md", "j")

    # Test 1b: agreement is counted per question. This once read a loop variable
    # left over from the judging loop, so every question was scored against the
    # last question's notes and 31 comparable pairs were reported as 2.
    results = [{"question": "q1", "notes": ["a.md"]}, {"question": "q2", "notes": ["b.md"]}]
    cached = {cache_key("q1", "a.md", "j1"): True, cache_key("q1", "a.md", "j2"): True,
              cache_key("q2", "b.md", "j1"): True, cache_key("q2", "b.md", "j2"): False}
    assert agreement(results, cached, "j1", "j2") == [True, False]

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
