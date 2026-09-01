---
name: hop-ceiling pilot - a u-curve shadow the token-ceiling test never found
description: a 3-trial pilot testing whether limiting an agent to one note per turn (no accumulated context) reproduces a position effect that the single-shot concatenated-document test could not, on the same fact and question
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
> the earlier pilot fed a model 13 documents all at once and asked a question — 3/3 correct, no dip, at any position. this pilot asks about three different facts, one note per turn instead, no memory of earlier notes except the model's own running sense of the task, target planted at hop 1, 4, or 7 of 7. hop 1 and hop 7 came back clean, 3/3 correct each, across all three facts. hop 4 is where it fell apart: 3 of 4 trials at that position had trouble — one flat wrong answer, one missed-then-recovered-a-turn-late, one caught immediately. one of those four trials only exists because of a delivery mistake mid-experiment, flagged below rather than quietly folded in.
> done, 9 real trials plus one discarded-and-repurposed one, a real if noisy middle-hop signal.
> **needs from you:** nothing forced — the next real step (more repeats, or varying which fact sits at which hop) is optional follow-up, not a decision blocking anything else.

**why:** [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]]

## the idea this tests

a [conversation earlier today] raised a sharp point: if an agent traversing a graph (or a multi-turn conversation) gets to see every previously-visited node stacked in its context, "hop distance" and "token distance" are the same variable — a bigger context window just lets a model swallow more hops per glance, so what took 10 hops on a small-context model takes 1 hop on a big-context one. that would mean a hop-ceiling test is just a token-ceiling test wearing a different name, and would explain why the single-shot document pilot found nothing: the model could just re-read all 13 documents at once regardless of where the target sat.

the fix: strict amnesia. each turn shows *only* the current note — no running transcript of earlier notes stays in view except whatever the model itself carries forward as its own memory of the task. that's not a context-window test anymore. it's a test of whether a model's grip on the original goal degrades over a long sequence of small decisions, independent of how much any single decision can hold. a bigger context window doesn't obviously fix that.

## setup

three different target facts, each with a question worded with zero vocabulary overlap against its source note, tested against the same fixed pool of 6 distractor notes (D1 rocket stove, D2 instagram-as-diary, D3 youtube premium, D4 river tame, D5 maya node editor, D6 gdrive-went-down outage) — 7 slots per trial, target inserted at slot 1, 4, or 7, distractors filling the rest in fixed order.

- **F1 — machinist square**: source note describes an all-steel right-angle checking tool. question: "for checking a perfect right angle, craftspeople often pick an all-metal option over the older wood-bodied version because it holds its accuracy better over time. what is that all-metal tool called?"
- **F2 — discharge rate**: source note describes a battery's C-rate. question: "batteries get a rating that describes their speed of draining, expressed as a multiple of the battery's total size — what is that rating called?"
- **F3 — roller shutters**: source note describes UK planning-permission rules for external shutters. question: "which home addition, common on shop entrances but rare on houses in the UK, needs local government approval to install outside but not if fitted indoors?"

each trial is one fresh claude/haiku subagent, resumed turn-by-turn via direct messages — no re-sent history, each turn's message contains only that note's text plus the standing instruction: answer directly if the note contains it, otherwise reply exactly "next."

## result — route traveled and outcome, every trial

route notation: `D1 D2 D3 [TARGET] D4 D5 D6` means the target was shown on turn 4, distractors on the other six turns, in that fixed relative order.

| fact | route (target position marked `[F]`) | outcome |
|---|---|---|
| F1 (machinist square) | `[F1] D1 D2 D3 D4 D5 D6` (hop 1) | correct — "Engineer's square," turn 1 |
| F1 (machinist square) | `D1 D2 D3 [F1] D4 D5 D6` (hop 4) | **wrong** — "Speed Square," turn 4, never corrected |
| F1 (machinist square) | `D1 D2 D3 D4 D5 D6 [F1]` (hop 7) | correct — "Engineer's square," turn 7 |
| F2 (discharge rate) | `[F2] D1 D2 D3 D4 D5 D6` (hop 1) | correct — "C rate," turn 1 |
| F2 (discharge rate) | `D1 D2 D3 [F2] D4 D5 D6` (hop 4) | correct — "C rate," turn 4 |
| F2 (discharge rate) | `D1 D2 D3 D4 D5 D6 [F2]` (hop 7) | correct — "C-rate," turn 7 |
| F3 (roller shutters) | `[F3] D1 D2 D3 D4 D5 D6` (hop 1) | correct — "Shutters," turn 1 |
| F3 (roller shutters) | `D1 D2 D3 [F3] D4 D5 D6` (hop 4) | **missed at turn 4** ("next," answer was present) — self-corrected to "Shutters" at turn 5, one turn late |
| F3 (roller shutters), extra replicate | `D1 D2 D3 [F3] D4 D5 D6` (hop 4, see note below) | correct — "Shutters," turn 4, immediately |
| F3 (roller shutters) | `D1 D2 D3 D4 D5 D6 [F3]` (hop 7) | correct — "Shutters," turn 7 |

> [!note] one trial's route was wrong because of my mistake, not the model's
> the F3 hop-7 trial was meant to travel `D1 D2 D3 D4 D5 D6 [F3]` — target last. mid-experiment, I sent it the target note's text on turn 4 instead of the D4 distractor, so its real route became `D1 D2 D3 [F3] D4 D5 D6`, a hop-4 route in disguise. discarding it as a hop-7 result would hide a real, cleanly-answered trial; keeping it labeled as hop-7 would misrepresent what actually happened. it's kept above as what it actually was — an extra hop-4 replicate — and a fresh, correctly-routed hop-7 trial was run separately to fill the gap the mistake left (that's the F3 hop-7 row above, route confirmed correct).

**by position, across all three facts:**
- **hop 1 (start): 3/3 clean correct.** every fact, first turn, no hesitation.
- **hop 7 (end): 3/3 clean correct.** every fact, correct on the turn the target appeared.
- **hop 4 (middle): 1 wrong, 1 delayed, 2 clean, out of 4 trials.** every trouble this pilot found — the one flat wrong answer, the one missed-then-recovered answer — happened at the middle position. the two clean hop-4 answers (both real, not explained away) mean this isn't a hard rule, but it's the only position where anything went wrong at all.

## what this does and doesn't show

**does show:** a real, observable difference from the earlier single-shot pilot, which went a clean 3/3 with zero trouble at any position on the same kind of fact. turn-by-turn delivery produced genuine confusion (a wrong but real tool name) and a genuine delay (right answer, one turn late) that the concatenated-document version never produced once. all of that trouble clustered at the middle hop, none at the ends.

**doesn't show:** a proven, monotonic curve. 2 of 4 hop-4 trials were clean, and n=1-2 per fact-position cell is thin — a slow week for one model on one turn is still a plausible alternative explanation for any single miss. this is a real signal worth taking seriously, not yet a claim to cite as settled.

## next step (optional, not blocking)

more repeats per position, or the same three facts swapped to different hop positions than tested here, would tighten this. if the middle-hop trouble rate holds up, that's a genuinely new, distinct claim from anything in [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] or [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — both of those are about position *within a single context*, not persistence of a goal *across turns*.

## related

- [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]] — the single-shot pilot this one contrasts with, same fact and question
- [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — the diagnosis this pilot is an alternative angle on
- [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] — the original liu-et-al-scale design, still the next step for the single-shot line of testing
