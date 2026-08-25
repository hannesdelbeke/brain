"""Rank unchecked markdown tasks in the vault by a time-based urgency score.

Zero install: no Obsidian plugin needed, it reads the .md files directly.

    python skills/pkm-metadata-indexer/urgent_tasks.py
    python skills/pkm-metadata-indexer/urgent_tasks.py --top 40 --min-score 0
    python skills/pkm-metadata-indexer/urgent_tasks.py --selfcheck

Task syntax, both fields optional, either Dataview inline fields or the
Tasks plugin emoji, so the same line also works if a plugin is added later:

    - [ ] file tax return [due:: 2027-01-31] [created:: 2026-08-25]
    - [ ] write the doc my manager asked for [created:: 2026-08-25]

Score, documented in `TODO how to highlight urgent tasks.md`:

    100 / max(3, days_until_due + 3) + days_since_created / 3

First term is the deadline shape, near zero far out, 33 on the due date.
Second term is the rot shape, one point per three days of sitting.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parents[2]

TASK_RE = re.compile(r"^\s*[-*] \[ \] (.+)$")
FIELD_RE = {
    "due": re.compile(r"\[due::\s*(\d{4}-\d{2}-\d{2})\s*\]|📅\s*(\d{4}-\d{2}-\d{2})"),
    "created": re.compile(r"\[created::\s*(\d{4}-\d{2}-\d{2})\s*\]|➕\s*(\d{4}-\d{2}-\d{2})"),
}
# Two tuning knobs. FLOOR sets the ceiling on the deadline term (100/3 = 33).
# ROT_DAYS is how many days of sitting buy one point, raise it to rot slower.
FLOOR = 3
ROT_DAYS = 3


def parse_field(name, text):
    match = FIELD_RE[name].search(text)
    if not match:
        return None
    return date.fromisoformat(match.group(1) or match.group(2))


def score(due, created, today):
    total = 0.0
    if due is not None:
        total += 100 / max(FLOOR, (due - today).days + FLOOR)
    if created is not None:
        total += (today - created).days / ROT_DAYS
    return total


def scan(vault, today):
    rows = []
    for path in sorted(vault.glob("*.md")):
        fenced = False
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
            match = None if fenced else TASK_RE.match(line)
            if not match:
                continue
            text = match.group(1)
            due, created = parse_field("due", text), parse_field("created", text)
            if due is None and created is None:
                continue
            rows.append((score(due, created, today), path.name, number, text.strip()))
    rows.sort(key=lambda row: -row[0])
    return rows


def selfcheck():
    today = date(2026, 8, 25)
    assert round(score(date(2026, 8, 25), None, today), 1) == 33.3, "due today tops out"
    assert round(score(date(2025, 1, 1), None, today), 1) == 33.3, "overdue is capped, not negative"
    assert round(score(date(2026, 9, 1), None, today), 1) == 10.0, "due in 7 days scores 10"
    assert round(score(date(2026, 9, 24), None, today), 1) == 3.0, "due in 30 days scores 3"
    assert round(score(None, date(2026, 5, 27), today), 1) == 30.0, "90 days of sitting scores 30"
    assert score(None, None, today) == 0.0, "no dates, no score"
    assert score(date(2026, 9, 1), date(2026, 8, 18), today) > score(date(2026, 9, 1), today, today), "older wins ties"
    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault", type=Path, default=VAULT)
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--min-score", type=float, default=1.0)
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()

    if args.selfcheck:
        selfcheck()
        return

    rows = [row for row in scan(args.vault, date.today()) if row[0] >= args.min_score]
    if not rows:
        print("no dated tasks found. Add [due:: YYYY-MM-DD] or [created:: YYYY-MM-DD] to a '- [ ]' line.")
        return
    for total, name, number, text in rows[: args.top]:
        print(f"{total:6.1f}  {text}")
        print(f"        {name}:{number}")


if __name__ == "__main__":
    main()
