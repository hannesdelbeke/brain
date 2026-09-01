---
energy: 5
sentiment:
- 5
sentiment-hash: '86656786'
sentiment-label:
- analytical
tags:
- planning
- self-reflection
- work
- solved
---

### problem
A [[task]] is mentioned, and you write it down.
The next day or week, it is mentioned again. You realize it's important, but you are also busy with several other tasks and forget about it the next day.

You might write it down today's daily note TODO.
You might add it to a planning board.
But somehow this task can still slip your mind, when working on several other important tasks.

### proposal
A planning system showing how often a task is mentioned, could help with prioritizing.

## Answer
The signal is how often a wikilink target is newly written, counted by day, read from [[git history]]. Not how many notes link to it today. The two are different numbers and only the first answers the question in the problem section.

Score, one point per day the target was written, decayed by age:

    sum over distinct days a target was mentioned of 0.5 ** (age_days / 30)

A mention written today is worth 1, one written 30 days ago is worth 0.5. A day counts once no matter how many times the link appears in it, so pasting the same link ten times in one sitting does not outrank writing it on ten separate days. That is the shape the problem describes: the same thing surfacing again next day or next week.

Why the other candidates lose:

- Wikilink in-degree from the `edges` table is the cheapest to compute and was tried first. It ranks [[Obsidian]] 88, Python 63, Maya 63, and the rest of the vault's permanent subjects. It measures how central a subject has always been, and a thing that keeps slipping your mind is not a hub, it is a small thing that came up three times last month. `edges` also stores only the current graph, with no dates, so it cannot express "again next week" at all.
- Free-text mention frequency in note bodies means a full text scan plus a guess at what counts as the same task. A wikilink is already the vault's canonical name for a thing, with aliases resolved. No new matching problem.
- Note view counts do not exist here. The `views:` frontmatter era ended in July 2026 because writing analytics into notes broke the recently-edited list and flooded git, see [[2026-07-22 follow up Obsidian viewcount]]. The counts now live in a plugin `data.json` in the main vault, and no plugin is installed in this clone. View count also measures reading, and the problem is about writing something down repeatedly.
- Recency of edits from git alone ranks whichever note you touched last, which you already know.

The output is a sorted terminal list with a block bar per row, not a rendered note. A generated markdown table would need writing a file, keeping it fresh, and handling renames, for a view of the same twenty five rows. The bar is the heatmap: it is a one line format string and it pastes into a note as a code block if it is ever wanted there.

The proposal above said planning system. What shipped is a read command, not a system. Nothing is stored, nothing has to be maintained, and the ranking is recomputed from git each time it is run. [[extract historic wikilinks from git]] concluded that a persisted historic link table was not worth its upkeep, and that still holds; this reads the same diffs on demand and keeps no table.

## Plan
1. Run `python skills/pkm-metadata-indexer/mention_heatmap.py`. It shells out to `git log -p` for the last 180 days, counts wikilinks on added lines, and prints the ranked list. About 1.7s, no index and no plugin needed.
2. Read the top fifteen and mark which rows are things you should be doing rather than things you happen to write about. That is the calibration.
3. If old work outranks live work, lower `HALF_LIFE_DAYS` in the script from 30 to 14. If the list churns too fast to be useful, raise it. It is the only knob.
4. When a heatmap row is something to act on, give it a due or created date so [[TODO how to highlight urgent tasks|urgent_tasks.py]] picks it up too. The heatmap says what keeps coming up, the urgency score says what is running out of time; they are separate lists on purpose.

Smallest first step: run the command once and look at the top five. The heatmap only sees things written as [[wikilink|wikilinks]], so if a recurring task shows up as plain prose it will not rank, and writing it as a link is the habit that makes the rest work.

Implementation is [[mention_heatmap.py]], documented as section 9 of the [[pkm metadata indexer]] skill, with a `--selfcheck` covering the decay values and the diff parsing.

#prioritizing #planning
[[visualize]]
[[priority]]
[[planning]]
