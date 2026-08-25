---
tags:
- technical
- pkm
- planning
---

A way to find which notes in this vault still describe a problem I never resolved, without reading 3200 notes.

## Signals

Unsolved problems in this vault look like one of four shapes:

1. A note with a `Problem`, `Issue`, `Bug` or `Error` heading and no `Solution`, `Fix`, `Answer`, `Conclusion` or `Workaround` heading. Around 79 notes match this on its own.
2. A title starting with `TODO `. That prefix is already used as an explicit "not done" marker, for example [[TODO link notes from calendar]].
3. Unchecked task boxes (`- [ ]`) left in the body.
4. Body phrases such as "unresolved", "doesn't work", "can't figure out", "no idea why", "TBD".

Semantic search is poor at this. Querying the embedding index for "unsolved problem open question" returns concept notes about questions ([[question]], [[deep questions]]) rather than notes containing an actual open problem, because the shape of an open problem is structural, not topical. Lexical and structural signals win here.

## Tool

`skills/pkm-metadata-indexer/find_open_problems.py` scores every note against those four signals and prints a ranked list. It reads markdown directly instead of the sqlite index, so it also works when the index is stale.

```bash
python skills/pkm-metadata-indexer/find_open_problems.py --top 30
python skills/pkm-metadata-indexer/find_open_problems.py --min-score 5
```

117 notes score 3 or higher on the first run.

## Retiring a problem

Once a note's problem is resolved and the resolution is written in the note, add `solved` to its frontmatter `tags`. Notes tagged `solved` score zero and disappear from the list. This is the only piece of state the method needs: no separate index of open problems to keep in sync, and the tag is also queryable from Obsidian search and Dataview.

Tag `solved` only when the note itself contains the resolution. A note that lists ideas or options is still open.

[[vault hybrid search]]
[[Obsidian improvements]]
[[problem solve techniques]]
