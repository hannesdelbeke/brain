"""Rank vault notes by how likely they describe an unsolved problem.

Scans markdown directly instead of the sqlite index, so it works on a stale or
missing index. Full vault scan takes about a second.

    python skills/pkm-metadata-indexer/find_open_problems.py
    python skills/pkm-metadata-indexer/find_open_problems.py --top 50 --min-score 4
    python skills/pkm-metadata-indexer/find_open_problems.py --self-test

Notes tagged `solved` are excluded. Tag a note `solved` once its resolution is
written down, and it drops out of this list for good.
"""
import argparse
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".obsidian", "skills", "image", "__pycache__"}

HEADING = re.compile(r"^#{1,6}\s+(.*)", re.M)
PROBLEM_HEADING = re.compile(r"problem|issue|bug|error|blocker|not work", re.I)
SOLVED_HEADING = re.compile(
    r"solution|fix|answer|conclusion|workaround|result|resolved", re.I)
OPEN_MARKER = re.compile(
    r"unsolved|unresolved|open question|still (don't|do not) know|not sure why|"
    r"can'?t figure|couldn'?t figure|no idea why|doesn'?t work|does not work|"
    r"stuck on|blocked by|TBD|FIXME|\bTODO\b", re.I)
OPEN_TASK = re.compile(r"^\s*[-*]\s+\[ \]", re.M)
SOLVED_TAG = re.compile(r"^tags:.*?^(?:\w|---)", re.M | re.S)


def has_solved_tag(text):
    head = text.split("---", 2)[1] if text.startswith("---") else ""
    return re.search(r"^\s*-?\s*solved\s*$", head, re.M) is not None


def score_note(text):
    """Return (score, reasons) for one note's raw markdown."""
    if has_solved_tag(text):
        return 0, []
    headings = HEADING.findall(text)
    score, reasons = 0, []
    if any(PROBLEM_HEADING.search(h) for h in headings):
        if not any(SOLVED_HEADING.search(h) for h in headings):
            score += 3
            reasons.append("problem heading, no solution heading")
    markers = {m.group(0).lower() for m in OPEN_MARKER.finditer(text)}
    if markers:
        score += 2
        reasons.append("markers: " + ", ".join(sorted(markers)[:3]))
    open_tasks = len(OPEN_TASK.findall(text))
    if open_tasks:
        score += min(open_tasks, 3)
        reasons.append(f"{open_tasks} open task(s)")
    return score, reasons


def scan(vault):
    for path in vault.rglob("*.md"):
        if SKIP_DIRS & set(p.name for p in path.parents):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        score, reasons = score_note(text)
        if path.stem.lower().startswith("todo"):
            score += 3
            reasons.append("TODO title")
        if score:
            yield score, path.relative_to(vault).as_posix(), reasons


def self_test():
    open_note = "## Problem\nit doesn't work\n\n- [ ] find out why\n"
    s, _ = score_note(open_note)
    assert s == 6, s
    # a solution heading and no open task drops it under the default cutoff
    closed = open_note.replace("- [ ] find out why", "## Solution\nturn it off")
    assert score_note(closed)[0] == 2, score_note(closed)
    tagged = "---\ntags:\n- technical\n- solved\n---\n" + open_note
    assert score_note(tagged)[0] == 0, score_note(tagged)
    assert score_note("plain note about cheese\n")[0] == 0
    print("ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--min-score", type=int, default=3)
    ap.add_argument("--vault", type=Path, default=VAULT)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    hits = sorted(scan(args.vault), reverse=True)
    hits = [h for h in hits if h[0] >= args.min_score]
    for score, rel, reasons in hits[:args.top]:
        print(f"{score:>3}  {rel}  ({'; '.join(reasons)})")
    print(f"\n{len(hits)} notes scoring >= {args.min_score}", file=sys.stderr)


if __name__ == "__main__":
    main()
