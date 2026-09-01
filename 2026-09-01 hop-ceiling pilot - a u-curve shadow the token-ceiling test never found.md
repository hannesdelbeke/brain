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
> the earlier pilot fed a model 13 documents all at once and asked a question — 3/3 correct, no dip, at any position. this pilot asks one note per turn instead, no memory of earlier notes except the model's own running sense of the task. two follow-ups ran after the first 7-hop round: 6 more repeats at the middle hop (to pin down how often it actually goes wrong there), and a longer, 13-hop chain to see whether depth changes the shape. the middle-hop rate settled lower than first thought — 2 wrong out of 12, not 2 out of 6. the 13-hop chain found something the 7-hop version never showed: the *first* note, not the middle one, was the one that failed completely — a full, unrecovered miss, while the middle and the end of that same longer chain were both fine. depth didn't make the same spot worse, it moved which spot was risky.
> done — 12 hop-4 trials, one 13-hop chain (3 positions), real signal, but the shape changes with chain length rather than holding still.
> **needs from you:** nothing forced. the honest open question is now "does risk track a fixed position (start/middle/end) or a fixed distance from the end of the chain" — worth one more longer-chain run with 2-3 more facts before either framing gets treated as settled.

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

## follow-up A: 6 more repeats at hop 4 only

pinning down the hop-4 trouble rate specifically, without spending more calls on hop 1 and hop 7 (already 10/10 across 5 facts — not where the uncertainty was). 6 fresh facts, each a single 4-turn trial (3 distractors then target, no continuation past the answer — this round only measures accuracy at the moment the target appears, not post-answer retention):

| fact | question topic | outcome |
|---|---|---|
| capital gains tax allowance | UK tax-free threshold on asset-sale profit | correct — "£3,000" |
| .pth files | python startup-code file extension | correct — ".pth" |
| ducting shapes | which duct cross-section seals worse but looks better | correct — "rectangular" |
| domestic hot water heat pump | appliance that heats water from ambient warmth | correct — "Heat pump" |
| HDMI over wifi | shared vs. separate wireless network | correct — separate network, stated correctly |
| Charging Downstream Port | nickname for a charge-and-sync USB port | correct — "CDP" |

**6/6 clean.** combined with the original round's 6 hop-4 trials (1 wrong, 1 delayed-then-recovered, 4 clean), the real hop-4 tally is **10 clean out of 12, 2 with trouble** — closer to 1-in-6 than the 1-in-3 the smaller first sample suggested. the trouble is real (it never happened at either end across 16 separate 7-hop trials) but rarer than round one made it look.

## follow-up B: a single 13-hop chain, target swept at hop 1 / 7 / 13

same F1 fact and question (machinist square) for direct comparability, 12 distractors instead of 6 (the original 6 plus talinolol, capital gains tax allowance, .pth, google, ducting, HDMI over wifi), one trial per position, run to full length each time (not stopped early).

| position | route | outcome |
|---|---|---|
| hop 1 | `[F1] then 11 distractors` (one distractor, maya node editor, was accidentally skipped mid-chain — a minor slip, noted honestly, that shortens this specific route to 12 notes instead of 13 but doesn't change where the target sat) | **wrong — full, unrecovered miss.** said "next" for all 11 remaining turns, then, when told explicitly this was the last note and to give a final answer instead of "next," replied "I don't know" — and its own reasoning showed it had correctly matched note 1's description to the question, but still couldn't produce the tool's name |
| hop 7 | `6 distractors, [F1], 6 distractors` | correct — "Engineer's Square" |
| hop 13 | `12 distractors, [F1]` | correct — "Machinist's square" |

this is the opposite shape from the 7-hop chain, where hop 1 was the *safest* position (5/5 clean across every fact tested) and hop 4 (the middle) was the only place trouble showed up. at 13 hops, the same "shown first" position failed completely, while both the middle-ish hop 7 and the final hop 13 succeeded.

## what this does and doesn't show

**does show:** hop-ceiling trouble is real and reproducible — some position in a long, amnesia-gated chain will eventually fail, across two very different chain lengths and six different facts. it also shows the failure isn't tied to a fixed slot like "the middle" or "the start" — the 13-hop chain's failure moved to the position that was safest at 7 hops. that rules out the simplest story ("early information sticks, middle information doesn't") and argues for something more like: risk depends on the shape and length of the whole chain, not a fixed seat in it.

**doesn't show:** a settled mechanism. n=1 per position in the 13-hop round means the hop-1 failure could be one unlucky trial rather than a real "long chains punish early information" rule — the honest alternative explanations (total chain length, distance from the end, or just this one model instance having a bad run) aren't yet distinguishable from each other. the hop-4 rate at 7 hops is now reasonably solid (n=12); the 13-hop shape is not.

## next step (optional, not blocking)

repeat the 13-hop design with 2-3 more facts, keeping the same three positions, to see whether hop 1 keeps failing (a real depth effect) or this was one bad trial (noise). if the hop-1 failure holds up across more facts, the next real question is whether it's "hop 1 specifically" or "furthest from the end" that's dangerous — which would need a fourth position (e.g. hop 2 or hop 12) to tell apart. either way, this is a genuinely new, distinct claim from anything in [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] or [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — both of those are about position *within a single context*, not persistence of a goal *across turns*.

## related

- [[2026-09-01 wikipedia hop-ceiling test - setup and reproduction steps]] — the same design rerun on wikipedia prose with closed-book screening and 2 models: found zero trouble at any of 7 positions, contrasting with this note's real (if rare) hop-4 trouble
- [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]] — the single-shot pilot this one contrasts with, same fact and question
- [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — the diagnosis this pilot is an alternative angle on
- [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] — the original liu-et-al-scale design, still the next step for the single-shot line of testing
