---
name: pilot design - bringing the u-curve back with real notes and paraphrased questions
description: a cheap pilot, then a scale-up plan, to re-test lost-in-the-middle without the exact-match shortcut that erased it in candidate 2's fourth experiment — real vault notes as documents, a paraphrased question instead of a unique lookup key
created: 2026-09-01
tags:
  - pkm
  - research
  - readability
  - llm
  - lost-in-the-middle
  - experiment-design
---

> [!summary] eli5
> candidate 2's u-curve test failed because the question had an exact-match shortcut (a serial number). this note designs a cheap fix: use real vault notes as the document stack instead of synthetic ones, and ask a question worded differently than the source note so there's no string to grep for. a tiny 3-trial pilot first, a full liu-et-al-scale run only if the pilot shows any signal.
> not run yet, design only.
> **needs from you:** approve running the 3-trial pilot on public vault notes — recommend yes, it's 3 subagent calls and graded by hand, cheapest possible way to find out if this fix actually works before spending on the full 18-24 call version.

**why:** [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]]

## the two changes, and why both at once

[[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] found one problem: a unique serial number let the model skip real position-robust search. fixing just the question wording while keeping synthetic near-duplicate documents still leaves an artificial document stack, less like liu et al.'s genuinely-distinct wikipedia passages than real notes already are for free.

- **real notes instead of synthetic ones** — this vault's [public](https://github.com/hannesdelbeke/brain) notes already span wildly different topics (woodworking, ai research, hardware reviews, gaming) with zero engineering needed to make them "genuinely different," the same property liu et al. got from real wikipedia passages.
- **a paraphrased question instead of a lookup key** — ask about a note's actual point in different words than the note itself uses, so there's no shared string between question and answer for the model to grep for.

## the pilot: 3 calls, hand-graded, cheapest possible test

1. pick 10-15 real notes from `public/`, spanning different topics, none obviously related to each other.
2. pick one as the **target** — something with one clear, statable fact or opinion (a recommendation, a specific number, a specific reason).
3. write **one question** about that fact, worded with no vocabulary overlap with the note's own phrasing — e.g. if the note says "most people prefer table saw," ask "which tool did most commenters favor for long straight cuts," not "which saw do people prefer."
4. build the same document stack three times, moving the target to position 1, the middle, and the last slot each time. everything else about the stack stays identical.
5. dispatch 3 fresh, blind claude/haiku subagents — one per stack — each given only the concatenated documents and the question, never told position is the variable.
6. grade the 3 answers by hand (correct / wrong), since n=3 doesn't need automated grading.

**what the result means:** if position 1 and last both answer correctly and the middle one doesn't (or is visibly weaker), that's the u-curve's shadow showing up even at this tiny scale — worth scaling up. if all three come back correct, either the fix isn't enough or the pilot is still too small to stress the effect (liu et al.'s own dip is more visible at 10-20+ documents than at this size) — scale up before concluding either way, per the design below.

## the scale-up: reuse the existing liu-et-al-scale design, swap two things

[[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] already has a ready-to-run 20-document, 3-position (1/10/20), 2-instance design (24 agent calls total, ~140K tokens). reuse it as-is, with two swaps:

- **documents**: real notes pulled from `public/`, curated into 3 sets of 20 for the 3 positions x 2 instances (60 notes total, or fewer reused across instances if topic diversity allows), instead of llm-generated synthetic recall notices.
- **questions**: one paraphrased question per instance about the target note's actual content, worded with no shared vocabulary with the note, instead of a "why was serial X recalled" lookup.

drop the formatting variable (flat/bold/chunked) from this run — it's not what's being tested here, and keeping the document separator fixed (a plain blank line) removes a variable that would otherwise confound a first attempt at just getting the base effect to show up at all. formatting can be reintroduced in a later run once the u-curve itself is confirmed reproducible.

grading changes too: a paraphrased answer can't be scored by exact-substring match the way "X493-22" could. score each answer by whether it names the same underlying fact as the target note (a human read, or a second fresh haiku subagent given the ground-truth fact and the candidate answer, asked only "does this answer state the same fact, yes or no").

**cost**: same order of magnitude as the existing design (~24-30 agent calls), since only the content source and grading method change, not the call count.

## related

- [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — the diagnosis this pilot is built to test
- [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] — the existing scale-up design this reuses almost entirely
- [[2026-09-01 adversarial literature check for candidate 2]] — the literature that named the exact-match shortcut as the likely cause
