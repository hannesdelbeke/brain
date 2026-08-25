"""Rank wikilink targets by how often they were newly written, over time.

Answers "what keeps coming up", not "what is linked a lot". A thing you write
down again next week is a thing that matters; a thing linked from 90 old notes
is just a hub. Only git knows the difference, so this reads git history, not
the sqlite index, whose `edges` table has no dates.

    python skills/pkm-metadata-indexer/mention_heatmap.py
    python skills/pkm-metadata-indexer/mention_heatmap.py --days 30 --top 40
    python skills/pkm-metadata-indexer/mention_heatmap.py --selfcheck

Score, documented in `Priority heatmap.md`:

    sum over distinct days a target was mentioned of 0.5 ** (age_days / 30)

A mention written today is worth 1, one written 30 days ago is worth 0.5. Days
count once no matter how many times the target appears that day, so pasting the
same link ten times in one sitting does not outrank writing it on ten days.
"""

import argparse
import collections
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parents[2]

# [[target]], [[target|alias]], [[target#heading]] -> target
LINK_RE = re.compile(r"\[\[([^\]|#^]+)")
STAMP_RE = re.compile(r"^C(\d+)$")
# One knob: how fast attention cools. Raise it to let older mentions keep weight.
HALF_LIFE_DAYS = 30


def git_log(vault, days):
    """Raw `git log -p` output, one C<unixtime> line per commit."""
    return subprocess.run(
        ["git", "-C", str(vault), "log", f"--since={days}.days",
         "--pretty=format:C%ct", "-U0", "--no-color", "--", "*.md"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout


def mention_days(log_text):
    """Map lowercased target -> (spelling as written, set of dates mentioned)."""
    seen = collections.defaultdict(set)
    spelling = {}
    day = None
    for line in log_text.splitlines():
        stamp = STAMP_RE.match(line)
        if stamp:
            day = datetime.fromtimestamp(int(stamp.group(1))).date()
            continue
        # only added lines; a removed mention is attention spent, not pending
        if day is None or not line.startswith("+") or line.startswith("+++"):
            continue
        for target in LINK_RE.findall(line):
            target = target.strip()
            if not target:
                continue
            spelling.setdefault(target.lower(), target)
            seen[target.lower()].add(day)
    return {key: (spelling[key], dates) for key, dates in seen.items()}


def score(dates, today):
    return sum(0.5 ** ((today - day).days / HALF_LIFE_DAYS) for day in dates)


def selfcheck():
    today = date(2026, 8, 25)
    assert score([today], today) == 1.0, "a mention today is worth one point"
    assert score([date(2026, 7, 26)], today) == 0.5, "30 days old is worth half"
    assert score([], today) == 0.0, "never mentioned, no score"
    assert score([today, today], today) == 2.0, "score sums over the days given"

    log = "\n".join([
        "C%d" % int(datetime(2026, 8, 25, 12).timestamp()),
        "+++ b/day two.md",
        "+ back on [[tax return]] again, see [[Todoist|the list]]",
        "+ and [[tax return]] once more in the same day",
        "-  dropped [[old idea]]",
        "C%d" % int(datetime(2026, 8, 24, 12).timestamp()),
        "+++ b/day one.md",
        "+ [[tax return#deadline]] came up",
    ])
    found = mention_days(log)
    assert set(found) == {"tax return", "todoist"}, found
    assert found["tax return"][1] == {date(2026, 8, 25), date(2026, 8, 24)}, "heading ref counts, same day counts once"
    assert found["todoist"][0] == "Todoist", "alias stripped, spelling kept"
    assert "old idea" not in found, "removed lines are not mentions"
    assert score(found["tax return"][1], today) > score(found["todoist"][1], today), "two days beat one"
    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault", type=Path, default=VAULT)
    parser.add_argument("--days", type=int, default=180, help="how far back to read git history")
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--min-score", type=float, default=1.0)
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()

    if args.selfcheck:
        selfcheck()
        return

    today = date.today()
    rows = [(score(dates, today), len(dates), spelling)
            for spelling, dates in mention_days(git_log(args.vault, args.days)).values()]
    rows = sorted((row for row in rows if row[0] >= args.min_score), reverse=True)
    if not rows:
        print(f"no wikilinks written in the last {args.days} days of git history.")
        return
    hottest = rows[0][0]
    for total, days, spelling in rows[: args.top]:
        bar = "█" * max(1, round(8 * total / hottest))
        print(f"{total:6.2f}  {bar:<8}  {days:2d}d  {spelling}")


if __name__ == "__main__":
    main()
