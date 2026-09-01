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
> the earlier pilot fed a model 13 documents all at once and asked a question — 3/3 correct, no dip, at any position. this pilot asks about five different facts instead, one note per turn, no memory of earlier notes except the model's own running sense of the task, target planted at hop 1, 4, or 7 of 7. hop 1 and hop 7 came back perfectly clean — 10/10 correct across all five facts, zero hesitation. hop 4 is the only place anything went wrong: 2 of 6 middle-position trials had trouble (one flat wrong answer, one missed-then-recovered-a-turn-late), the other 4 were clean. the signal is real but weaker and noisier than the first three-fact round alone suggested — the two facts added in the second round produced zero trouble at any position.
> done, 15 real trials plus one discarded-and-repurposed one, a real but noisy middle-hop signal that got weaker, not stronger, as the sample grew.
> **needs from you:** nothing forced — the next real step (more repeats, or a longer chain past 7 hops) is optional follow-up, not a decision blocking anything else.

**why:** [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]]

## the idea this tests

a [conversation earlier today] raised a sharp point: if an agent traversing a graph (or a multi-turn conversation) gets to see every previously-visited node stacked in its context, "hop distance" and "token distance" are the same variable — a bigger context window just lets a model swallow more hops per glance, so what took 10 hops on a small-context model takes 1 hop on a big-context one. that would mean a hop-ceiling test is just a token-ceiling test wearing a different name, and would explain why the single-shot document pilot found nothing: the model could just re-read all 13 documents at once regardless of where the target sat.

the fix: strict amnesia. each turn shows *only* the current note — no running transcript of earlier notes stays in view except whatever the model itself carries forward as its own memory of the task. that's not a context-window test anymore. it's a test of whether a model's grip on the original goal degrades over a long sequence of small decisions, independent of how much any single decision can hold. a bigger context window doesn't obviously fix that.

## setup

five different target facts, each with a question worded with zero vocabulary overlap against its source note, tested against the same fixed pool of 6 distractor notes (D1 rocket stove, D2 instagram-as-diary, D3 youtube premium, D4 river tame, D5 maya node editor, D6 gdrive-went-down outage) — 7 slots per trial, target inserted at slot 1, 4, or 7, distractors filling the rest in fixed order.

- **F1 — machinist square**: source note describes an all-steel right-angle checking tool. question: "for checking a perfect right angle, craftspeople often pick an all-metal option over the older wood-bodied version because it holds its accuracy better over time. what is that all-metal tool called?"
- **F2 — discharge rate**: source note describes a battery's C-rate. question: "batteries get a rating that describes their speed of draining, expressed as a multiple of the battery's total size — what is that rating called?"
- **F3 — roller shutters**: source note describes UK planning-permission rules for external shutters. question: "which home addition, common on shop entrances but rare on houses in the UK, needs local government approval to install outside but not if fitted indoors?"
- **F4 — 7DRL roguelike**: source note describes an old unfinished game-jam project. question: "in an old, unfinished game-jam project, what was the one type of art asset the creator still made sure to keep backups of?"
- **F5 — Blender window size**: source note describes measuring a window's title bar height. question: "when someone checked a window's title bar height using a separate screen-measurement utility instead of code, what height in pixels did that utility report?"

each trial is one fresh claude/haiku subagent, resumed turn-by-turn via direct messages — no re-sent history, each turn's message contains only that note's text plus the standing instruction: answer directly if the note contains it, otherwise reply exactly "next." F4 and F5 were added as a second round, on the same distractor pool and hop structure, specifically to check whether the trouble seen in F1-F3 held up with more data.

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
| F4 (7DRL roguelike) | `[F4] D1 D2 D3 D4 D5 D6` (hop 1) | correct — "sprites," turn 1 |
| F4 (7DRL roguelike) | `D1 D2 D3 [F4] D4 D5 D6` (hop 4) | correct — "sprites," turn 4 |
| F4 (7DRL roguelike) | `D1 D2 D3 D4 D5 D6 [F4]` (hop 7) | correct — "Sprites," turn 7 |
| F5 (Blender window size) | `[F5] D1 D2 D3 D4 D5 D6` (hop 1) | correct — "28," turn 1 |
| F5 (Blender window size) | `D1 D2 D3 [F5] D4 D5 D6` (hop 4) | correct — "28," turn 4 |
| F5 (Blender window size) | `D1 D2 D3 D4 D5 D6 [F5]` (hop 7) | correct — "28," turn 7 |

> [!note] one trial's route was wrong because of my mistake, not the model's
> the F3 hop-7 trial was meant to travel `D1 D2 D3 D4 D5 D6 [F3]` — target last. mid-experiment, I sent it the target note's text on turn 4 instead of the D4 distractor, so its real route became `D1 D2 D3 [F3] D4 D5 D6`, a hop-4 route in disguise. discarding it as a hop-7 result would hide a real, cleanly-answered trial; keeping it labeled as hop-7 would misrepresent what actually happened. it's kept above as what it actually was — an extra hop-4 replicate — and a fresh, correctly-routed hop-7 trial was run separately to fill the gap the mistake left (that's the F3 hop-7 row above, route confirmed correct).

**by position, across all five facts (16 trials counting the discarded-and-repurposed one):**
- **hop 1 (start): 5/5 clean correct.** every fact, first turn, no hesitation.
- **hop 7 (end): 5/5 clean correct.** every fact, correct on the turn the target appeared.
- **hop 4 (middle): 4/6 clean, 2 with real trouble.** F1 gave a flat wrong answer that never corrected. F3's first replicate missed the answer on the turn it appeared and only recovered one turn late. F2, F4, F5, and F3's second (mistake-derived) replicate were all clean. every piece of trouble this pilot found, across both rounds, happened at the middle position — but the middle position is no longer *mostly* trouble, it's now a minority of middle trials (2 of 6).

## what this does and doesn't show

**does show:** a real, observable difference from the earlier single-shot pilot, which went a clean 3/3 with zero trouble at any position on the same kind of fact. across 16 hop-ceiling trials, hop 1 and hop 7 combined are a perfect 10/10 — no wrong answer, no delay, ever, at either end. every single instance of trouble in this whole pilot, both rounds, happened at hop 4. that clustering held up as the sample doubled.

**doesn't show:** a strong or monotonic effect. adding two more facts (F4, F5) added zero new trouble — both went 3/3 clean, including at hop 4. the honest reading after 5 facts: middle-hop trouble is real (it never once appeared at either end) but is more like a 1-in-3 chance at the middle than a reliable dip, at least at this depth and on this model. a slow moment for the model on one particular fact is still a live alternative explanation for either of the two failures.

## next step (optional, not blocking)

two directions, either would sharpen this more than blindly adding facts at the same depth: more repeats specifically at hop 4 (to pin down whether it's closer to 1-in-3 or something else), or a longer chain than 7 hops — this pilot has never shown a dip get *worse*, only whether one appears at all at a single middle point, and a real agent session runs far more than 7 turns. if either line holds up, that's a genuinely new, distinct claim from anything in [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] or [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — both of those are about position *within a single context*, not persistence of a goal *across turns*.

## related

- [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]] — the single-shot pilot this one contrasts with, same fact and question
- [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — the diagnosis this pilot is an alternative angle on
- [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] — the original liu-et-al-scale design, still the next step for the single-shot line of testing
