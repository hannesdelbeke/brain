"""DEGENERACY CHECK FOR FORCED-CHOICE JUDGEMENT RUNS.

A language model running a long series of forced-choice judgements may run out
of patience and start repeating a constant answer. The output remains perfectly
well-formed - every question gets an answer - so nothing downstream would
complain. But if the task layout pairs related questions across the two halves,
a constant tail corrupts the result systematically rather than randomly.

A judge failing these checks is unusable and must be rerun, not corrected.
There is no way to recover a content judgement from a constant.

This script detects three signs of degeneracy:

  1. LONGEST RUN of one answer. Under independent judging with rate p, the
     longest run in n items is about log(n)/log(1/p). Anything far past that
     is a model repeating itself rather than deciding.

  2. FIRST-HALF against SECOND-HALF answer distribution. A judge whose answer
     rate shifts hard between halves has changed behaviour mid-task.

  3. POSITIONAL DRIFT, the answer rate in successive blocks, so the point of
     collapse is visible rather than inferred.

Usage:
  python judge_health.py ANSWERS.json [ANSWERS.json ...]

where each file is a JSON object mapping question number (as string or int) to
a single-character answer. Prints a per-file verdict of either "DEGENERATE,
UNUSABLE" or "looks healthy", and exits 1 if any file is degenerate.
"""
import json
import math
import sys
from pathlib import Path


def check(name, ans):
    """Check one answer file for degeneracy. Returns True if healthy."""
    seq = [ans[i] for i in range(1, len(ans) + 1)]
    n = len(seq)

    print("=" * 74)
    print(f"{name}")
    print("=" * 74)

    # Count answer rates
    chars = sorted(set(seq))
    rates = {c: seq.count(c) / n for c in chars}
    rate_str = "  overall  " + "  ".join(f"{c} {rates[c]:.0%}" for c in chars)
    print(rate_str)

    # Check longest run
    best, cur, bc = 0, 0, None
    prev = None
    for c in seq:
        cur = cur + 1 if c == prev else 1
        prev = c
        if cur > best:
            best, bc = cur, c

    # Expected longest run under independent judging
    p = max(rates.values())
    exp = math.log(n) / math.log(1 / p) if 0 < p < 1 else float("inf")
    print(f"  longest run: {best} of '{bc}'   expected under independent "
          f"judging ~{exp:.0f}")
    verdict_run = best > 4 * exp

    # Check first-half vs second-half distribution shift
    h1 = seq[: n // 2]
    h2 = seq[n // 2:]
    # Use the most common answer for the shift check
    most_common = max(chars, key=lambda c: rates[c])
    r1 = h1.count(most_common) / len(h1)
    r2 = h2.count(most_common) / len(h2)
    print(f"  '{most_common}' rate  first half {r1:.0%}   second half {r2:.0%}   "
          f"shift {r2 - r1:+.0%}")
    verdict_half = abs(r2 - r1) > 0.25

    # Show drift by block of 50
    print("  drift by block of 50:")
    line = "    "
    for i in range(0, n, 50):
        blk = seq[i:i + 50]
        rate_in_block = blk.count(most_common) / len(blk)
        line += f"{rate_in_block:.0%}".rjust(6)
    print(line + f"   <- share answering '{most_common}'")

    bad = verdict_run or verdict_half
    print(f"\n  VERDICT: {'DEGENERATE, UNUSABLE' if bad else 'looks healthy'}")
    if verdict_run:
        print(f"    longest run {best} is more than 4x the expected {exp:.0f}")
    if verdict_half:
        print(f"    answer distribution shifts {r2 - r1:+.0%} between halves")
    print()
    return not bad


def main():
    if len(sys.argv) < 2:
        print("usage: python judge_health.py ANSWERS.json [...]", file=sys.stderr)
        sys.exit(1)

    all_ok = True
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"error: {path} does not exist", file=sys.stderr)
            all_ok = False
            continue

        try:
            data = json.loads(path.read_text())
        except Exception as e:
            print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
            all_ok = False
            continue

        # Normalize keys to integers
        try:
            ans = {int(k): v for k, v in data.items()}
        except ValueError as e:
            print(f"error: {path} has non-numeric keys: {e}", file=sys.stderr)
            all_ok = False
            continue

        # Check that we have contiguous 1..n
        if not ans or sorted(ans) != list(range(1, len(ans) + 1)):
            print(f"error: {path} does not have contiguous 1..n keys, "
                  f"got {len(ans)} entries", file=sys.stderr)
            all_ok = False
            continue

        ok = check(path.name, ans)
        all_ok = all_ok and ok

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
