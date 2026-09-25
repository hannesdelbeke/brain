"""Two-arm benchmark for search latency and precision.

A latency win that costs precision is not a win. This tool reports both metrics
side by side so you can answer "did this change make search better or worse" in
one command, with the delta between arms showing the direction of each metric.

Latency is measurable without the judge (--no-judge skips precision entirely and
costs no API calls). Precision reuses the shared cached judge from eval_judge.py
so verdicts are comparable across evals.

    python eval_bench.py --vault brain --questions eval_questions/kepano.json \
        --arm-a "expand=1,rerank=1" --arm-b "expand=0,rerank=1" --reps 5

All /search calls pass origin="eval-<label>" so telemetry can exclude them from
co-retrieval edges. An origin not starting with "eval-" is rejected.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

import eval_judge

DEFAULT_DAEMON = "http://127.0.0.1:44771"
JUDGE_CACHE = Path.home() / ".pkm" / "bench-judgements.json"
JUDGE_MODEL = os.environ.get("MODEL", "gemini-2.5-flash")


def parse_arm_params(spec: str) -> dict[str, str]:
    """Parse comma-separated key=value pairs into a dict.

    Raises ValueError if the spec is malformed (missing = or empty key/value).
    """
    if not spec.strip():
        return {}
    params = {}
    for pair in spec.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise ValueError(f"Malformed arm parameter (missing '='): {pair!r}")
        key, value = pair.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key or not value:
            raise ValueError(f"Empty key or value in parameter: {pair!r}")
        params[key] = value
    return params


def validate_origin(origin: str) -> None:
    """Raise ValueError if origin does not start with the required prefix.

    co_retrieval.py requires SYNTHETIC_ORIGIN_PREFIX = "eval-" to exclude synthetic
    queries from association edges. An origin that does not start with "eval-" would
    corrupt the ranker by treating benchmark queries as real human traffic.
    """
    if not origin.startswith("eval-"):
        raise ValueError(
            f"Origin must start with 'eval-' to exclude from telemetry; got {origin!r}"
        )


def search(vault: str, question: str, limit: int, origin: str, arm_params: dict[str, str], daemon: str) -> tuple[list[dict], float]:
    """Issue one search query and return (results, wall_ms).

    wall_ms is the caller's full round-trip, which is the number a user feels.
    The daemon's own `took_ms` is deliberately not used: it is reported per
    corpus but carries the whole query's total, so it cannot be attributed to
    one arm's work. See the vault note on entity expansion latency.

    perf_counter rather than time.time because this is an interval measurement
    and time.time can step backwards under an NTP adjustment mid-run.
    """
    params = {"vault": vault, "q": question, "limit": limit, "origin": origin}
    params.update(arm_params)

    url = f"{daemon}/search?" + urlencode(params)
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=120) as response:
        data = json.load(response)
    wall_ms = (time.perf_counter() - start) * 1000

    return data["results"], wall_ms


def percentile(values: list[float], p: float) -> float:
    """Compute the p-th percentile (0 <= p <= 1) of sorted values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = p * (len(sorted_values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def judged_content(hit: dict) -> str:
    """The text the judge scores for one search hit.

    `text` rather than `snippet`, because the daemon returns `snippet: null` for
    a large minority of hits -- 36 of 150 over 15 questions against the 16k-section
    corpus, 24%. `hit.get("snippet", "")` returns None for those, since the key is
    present and null rather than absent, and None formats into the judge prompt as
    the literal word "None". The judge then scores a blank note, rules it useless,
    and precision reads low for a result that may have been perfectly good. `text`
    was non-empty on all 150 of those hits, is the fuller field (median 660 chars
    against snippet's 162), and is closer to the section text eval_rerank.py
    judges on, which keeps the two harnesses' numbers comparable.

    Both arms were checked to return byte-identical text for the same (path, line),
    so one cached verdict per (question, path) is legitimate here -- the constraint
    eval_judge.cache_key documents.
    """
    return str(hit.get("text") or hit.get("snippet") or "")


def measure_latency(vault: str, questions: list[tuple[str, str]], limit: int, origin: str,
                    arm_params: dict[str, str], reps: int, daemon: str) -> dict[str, float]:
    """Run each question `reps` times and return p50 and p95 wall-clock, with the
    sample count so a reader can tell a stable number from a noisy one."""
    wall_times = []

    for question, _group in questions:
        for _ in range(reps):
            _results, wall_ms = search(vault, question, limit, origin, arm_params, daemon)
            wall_times.append(wall_ms)

    return {
        "p50_wall_ms": percentile(wall_times, 0.5),
        "p95_wall_ms": percentile(wall_times, 0.95),
        "count": len(wall_times),
    }


def judge_precision(vault: str, questions: list[tuple[str, str]], limit: int, origin: str,
                   arm_params: dict[str, str], cache: dict, failures: dict[str, int], daemon: str) -> list[dict]:
    """Run each question once, judge all results, and return per-question metrics.

    Mutates `cache` and `failures` via eval_judge.judge_all. Returns a list of dicts
    with keys: question, group, metrics (containing p3, p5, p10, first_rank, has_useful).
    """
    results = []
    unjudgeable = 0
    for question, group in questions:
        hits, _wall_ms = search(vault, question, limit, origin, arm_params, daemon)
        paths = [hit["path"] for hit in hits]

        # Build prompts for any unjudged pairs
        pending = []
        for hit in hits:
            key = eval_judge.cache_key(question, hit["path"], JUDGE_MODEL)
            if key not in cache:
                content = judged_content(hit)
                if not content:
                    # Counted and reported rather than sent: judging an empty note
                    # spends an API call to manufacture a "not useful" verdict that
                    # then caches and depresses every later run's precision.
                    unjudgeable += 1
                    continue
                prompt = eval_judge.JUDGE_PROMPT.format(question=question, content=content)
                pending.append((question, hit["path"], JUDGE_MODEL, prompt))

        eval_judge.judge_all(pending, cache, failures, workers=8)

        # Compute metrics from verdicts
        verdicts = {hit["path"]: cache.get(eval_judge.cache_key(question, hit["path"], JUDGE_MODEL))
                    for hit in hits}
        metrics = eval_judge.compute_metrics(paths, verdicts)

        results.append({
            "question": question,
            "group": group,
            "metrics": metrics,
        })

    if unjudgeable:
        print(f"  note: {unjudgeable} hits carried no text and were left unjudged; "
              f"they count as not useful", flush=True)

    return results


def report_latency(arm_a_name: str, arm_a_latency: dict, arm_b_name: str, arm_b_latency: dict) -> None:
    """Print latency comparison side by side with deltas."""
    print("\n=== LATENCY ===", flush=True)
    print(f"  {arm_a_latency['count']} queries per arm\n", flush=True)

    a_p50 = arm_a_latency["p50_wall_ms"]
    b_p50 = arm_b_latency["p50_wall_ms"]
    a_p95 = arm_a_latency["p95_wall_ms"]
    b_p95 = arm_b_latency["p95_wall_ms"]

    delta_p50 = b_p50 - a_p50
    delta_p95 = b_p95 - a_p95

    print(f"  p50 wall-clock (ms):", flush=True)
    print(f"    {arm_a_name}: {a_p50:.1f}", flush=True)
    print(f"    {arm_b_name}: {b_p50:.1f}", flush=True)
    print(f"    delta: {delta_p50:+.1f} ms ({delta_p50/a_p50:+.1%})" if a_p50 else f"    delta: n/a", flush=True)

    print(f"\n  p95 wall-clock (ms):", flush=True)
    print(f"    {arm_a_name}: {a_p95:.1f}", flush=True)
    print(f"    {arm_b_name}: {b_p95:.1f}", flush=True)
    print(f"    delta: {delta_p95:+.1f} ms ({delta_p95/a_p95:+.1%})" if a_p95 else f"    delta: n/a", flush=True)


def report_precision(arm_a_name: str, arm_a_results: list[dict], arm_b_name: str, arm_b_results: list[dict]) -> None:
    """Print precision comparison side by side with deltas."""
    print("\n=== PRECISION ===", flush=True)

    def aggregate(results: list[dict]) -> dict:
        p3_useful = sum(r["metrics"]["p3"][0] for r in results)
        p3_total = sum(r["metrics"]["p3"][1] for r in results)
        p5_useful = sum(r["metrics"]["p5"][0] for r in results)
        p5_total = sum(r["metrics"]["p5"][1] for r in results)
        p10_useful = sum(r["metrics"]["p10"][0] for r in results)
        p10_total = sum(r["metrics"]["p10"][1] for r in results)
        first_ranks = [r["metrics"]["first_rank"] for r in results if r["metrics"]["first_rank"]]
        mean_first = sum(first_ranks) / len(first_ranks) if first_ranks else None

        return {
            "p3": (p3_useful, p3_total),
            "p5": (p5_useful, p5_total),
            "p10": (p10_useful, p10_total),
            "mean_first_rank": mean_first,
            "answered": len(first_ranks),
            "total": len(results),
        }

    a_agg = aggregate(arm_a_results)
    b_agg = aggregate(arm_b_results)

    print(f"  {len(arm_a_results)} questions\n", flush=True)

    for k in [3, 5, 10]:
        a_useful, a_total = a_agg[f"p{k}"]
        b_useful, b_total = b_agg[f"p{k}"]
        a_pct = a_useful / a_total if a_total else 0
        b_pct = b_useful / b_total if b_total else 0
        delta_pct = b_pct - a_pct

        print(f"  precision@{k}:", flush=True)
        print(f"    {arm_a_name}: {a_useful}/{a_total} = {a_pct:.1%}", flush=True)
        print(f"    {arm_b_name}: {b_useful}/{b_total} = {b_pct:.1%}", flush=True)
        print(f"    delta: {delta_pct:+.1%}", flush=True)

    a_mean = a_agg["mean_first_rank"]
    b_mean = b_agg["mean_first_rank"]

    print(f"\n  mean first useful rank:", flush=True)
    print(f"    {arm_a_name}: {a_mean:.1f}" if a_mean else f"    {arm_a_name}: none", flush=True)
    print(f"    {arm_b_name}: {b_mean:.1f}" if b_mean else f"    {arm_b_name}: none", flush=True)
    if a_mean and b_mean:
        delta_mean = b_mean - a_mean
        print(f"    delta: {delta_mean:+.1f}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Two-arm benchmark for search latency and precision.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--vault", required=True, help="Vault name (e.g., brain)")
    parser.add_argument("--questions", required=True, help="Path to question set JSON")
    parser.add_argument("--arm-a", required=True, help="Arm A params (comma-separated key=value)")
    parser.add_argument("--arm-b", required=True, help="Arm B params (comma-separated key=value)")
    parser.add_argument("--limit", type=int, default=20, help="Number of results per query (default: 20)")
    parser.add_argument("--reps", type=int, default=3, help="Repetitions per query for latency (default: 3)")
    parser.add_argument("--origin", default="eval-bench", help="Origin label for telemetry (must start with 'eval-', default: eval-bench)")
    parser.add_argument("--daemon", help="Search daemon base URL (default: PKM_DAEMON_URL env or http://127.0.0.1:44771)")
    parser.add_argument("--no-judge", action="store_true", help="Skip precision phase (latency only)")

    args = parser.parse_args()

    # Resolve daemon URL: --daemon flag > PKM_DAEMON_URL env > default
    daemon = args.daemon or os.environ.get("PKM_DAEMON_URL") or DEFAULT_DAEMON

    # Validate origin prefix
    validate_origin(args.origin)

    # Parse arm parameters
    try:
        arm_a_params = parse_arm_params(args.arm_a)
        arm_b_params = parse_arm_params(args.arm_b)
    except ValueError as e:
        print(f"Error parsing arm parameters: {e}", file=sys.stderr)
        sys.exit(1)

    # Load questions
    questions = eval_judge.load_questions(args.questions)
    if not questions:
        print(f"No questions loaded from {args.questions}", file=sys.stderr)
        sys.exit(1)

    print(f"Benchmark: {len(questions)} questions, {args.reps} reps per query", flush=True)
    print(f"  Arm A: {args.arm_a or '(baseline)'}", flush=True)
    print(f"  Arm B: {args.arm_b or '(baseline)'}", flush=True)
    print(f"  Origin: {args.origin}", flush=True)

    # LATENCY PHASE
    print("\nMeasuring latency...", flush=True)
    arm_a_latency = measure_latency(args.vault, questions, args.limit, args.origin, arm_a_params, args.reps, daemon)
    arm_b_latency = measure_latency(args.vault, questions, args.limit, args.origin, arm_b_params, args.reps, daemon)

    report_latency("A", arm_a_latency, "B", arm_b_latency)

    # PRECISION PHASE
    if not args.no_judge:
        print("\nMeasuring precision...", flush=True)
        cache = eval_judge.load_cache(JUDGE_CACHE)
        failures = defaultdict(int)

        arm_a_results = judge_precision(args.vault, questions, args.limit, args.origin, arm_a_params, cache, failures, daemon)
        arm_b_results = judge_precision(args.vault, questions, args.limit, args.origin, arm_b_params, cache, failures, daemon)

        eval_judge.save_cache(JUDGE_CACHE, cache)

        if failures[JUDGE_MODEL]:
            print(f"\nWARNING: {failures[JUDGE_MODEL]} judge calls failed", flush=True)

        report_precision("A", arm_a_results, "B", arm_b_results)
    else:
        print("\n(precision phase skipped via --no-judge)", flush=True)


if __name__ == "__main__":
    main()
