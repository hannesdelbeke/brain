---
name: wikipedia hop-ceiling test - setup and reproduction steps
description: reproducible setup for testing the hop-ceiling position effect on real wikipedia prose instead of vault notes, with closed-book contamination screening and a cross-model comparison — documented step by step as it runs, before results are known
created: 2026-09-01
tags:
  - pkm
  - research
  - readability
  - llm
  - lost-in-the-middle
  - experiment-design
  - reproducibility
---

> [!summary] eli5
> the earlier hop-ceiling pilots used personal vault notes, which vary wildly in quality and length. this note runs the same kind of test on real wikipedia paragraphs instead — closer to the original lost-in-the-middle paper's own design — with a closed-book contamination check and two models tested side by side. result: **10/10 correct, every position (1 through 7), both models, zero trouble anywhere.** the vault-note version found real (if rare) trouble at the middle hop; the wikipedia version, same design, same protocol, found none at all.
> done. 10 clean trials plus 3 routing mistakes on my end, all caught and fixed (documented below, not hidden).
> **needs from you:** worth deciding whether the vault-note pilot's hop-4 trouble was really about turn-count/amnesia, or was partly an artifact of terser, more ambiguous personal-note phrasing that wikipedia's cleaner prose doesn't have. this note can't settle that alone — recommend treating "amnesia across turns causes trouble" as unconfirmed until a version controls for prose style directly, since the two variables (document source and clean-fact screening) both changed at once here.

**why:** [[2026-09-01 hop-ceiling pilot - a u-curve shadow the token-ceiling test never found]]

## why wikipedia, and the risk it introduces

the vault-note pilots used real personal notes because they're naturally topically diverse the way liu et al.'s wikipedia passages were — but a personal vault has notes ranging from one-line fragments to full technical writeups, an inconsistency the vault itself doesn't have a fix for. wikipedia gives that same natural diversity with far more consistent paragraph length and register, and is the literal source material liu et al.'s own "lost in the middle" paper used.

the cost: wikipedia content is very likely in a model's training data. if the model already knows the target fact, it can answer correctly without reading anything given to it — which would look identical to "the model found it" in every position, silently invalidating the whole test. the fix, taken directly from liu et al.'s own methodology: a **closed-book control** — ask the target question with zero context, before running any position trial. if the model can already answer it, or answers with a confident wrong-but-specific guess (which turns out to matter, see below), that fact is contaminated and gets thrown out.

## closed-book screening — round 1 (rejected)

**candidate fact:** 20000 Varuna (a trans-Neptunian object), synodic rotation period, sourced from [20000 Varuna](https://en.wikipedia.org/wiki/20000_Varuna): "6.343572±0.000006 h."

**question:** "how many hours does it take the trans-Neptunian object 20000 Varuna to complete one full rotation on its axis?"

**screening method:** a fresh subagent per model, no memory of this conversation, prompted "Answer this question from your own knowledge only, no tools, no searching. If you don't know, say 'I don't know' — do not guess a plausible-sounding number." — and the subagent's actual tool-call count checked afterward (0 for both), confirming neither one cheated by fetching the answer instead of answering from training memory.

**result:**
- **sonnet:** "I don't know." — clean, passes.
- **haiku:** "approximately 3.17 hours" — a confident, specific, *wrong* answer (real value is 6.34h, roughly double). this isn't a fabricated hallucination out of nowhere — 3.2h was Varuna's real, published rotation period estimate before later observations revised it to 6.34h (a lightcurve-period doubling ambiguity, a known thing that happens with asteroid rotation studies) — so haiku most likely memorized an outdated but real number from training data.

**verdict:** rejected. haiku has a real prior belief about this specific fact, which is exactly the contamination the screening step exists to catch — an outdated-but-confident answer is just as disqualifying as a correct one, since it means the model isn't approaching the in-context passage with a blank slate.

## closed-book screening — round 2 (passed)

**candidate fact:** Zavodovski Island (part of the Traversay Islands, South Sandwich Islands), peak elevation, sourced from [Traversay Islands](https://en.wikipedia.org/wiki/Traversay_Islands): "551 metres (1,808 feet) above sea level."

**question:** "how many metres above sea level is the highest point of Zavodovski Island?"

**screening method:** identical to round 1, both models, fresh subagents, tool-use count checked (0 for both, confirming no lookup).

**result:** **sonnet:** "I don't know." **haiku:** "I don't know the exact elevation of Zavodovski Island's highest point." both clean. fact cleared for use in both models.

## document pool

target plus 8 distractor paragraphs pulled from wikipedia (6 used in the main 7-hop chain, 2 held as spares), one paragraph each, topically unrelated to the target and to each other: [Vaquita](https://en.wikipedia.org/wiki/Vaquita), [Franz Josef Land](https://en.wikipedia.org/wiki/Franz_Josef_Land), [Tokelau](https://en.wikipedia.org/wiki/Tokelau), [Rapa Nui language](https://en.wikipedia.org/wiki/Rapa_Nui_language), [Lonesome George](https://en.wikipedia.org/wiki/Lonesome_George), [Danakil Depression](https://en.wikipedia.org/wiki/Danakil_Depression) — used, in that fixed order (D1-D6) — plus [Möbius strip](https://en.wikipedia.org/wiki/M%C3%B6bius_strip) and [Basking shark](https://en.wikipedia.org/wiki/Basking_shark), unused spares.

**why every position, not 3 samples:** every prior round (both the vault-note pilots and the 13-hop chain) only ever tested 3 positions per chain (1/4/7 or 1/7/13) — enough to notice trouble exists, not enough to rule out the specific positions picked being a coincidence. this round tests **every position in a 7-hop chain (1 through 7)** with haiku, then re-checks 3 of those positions (1, 4, 7) with sonnet, so any shape found isn't assumed to be model-specific.

**protocol, unchanged from the vault-note pilots:** one fresh subagent per trial, resumed turn-by-turn via direct messages, each turn showing only that document's text plus the standing instruction (answer directly, or reply exactly "next"). no re-sent history — the only memory available to the model is whatever it carries forward itself.

## result

| position | model | route (target marked `[T]`) | outcome |
|---|---|---|---|
| 1 | haiku | `[T] D1 D2 D3 D4 D5 D6` | correct — 551, turn 1 |
| 2 | haiku | `D1 [T] D2 D3 D4 D5 D6` | correct — 551, turn 2 (after a routing mistake, see below) |
| 3 | haiku | `D1 D2 [T] D3 D4 D5 D6` | correct — 551, turn 3 (confirmed twice — see below) |
| 4 | haiku | `D1 D2 D3 [T] D4 D5 D6` | correct — 551, turn 4 |
| 5 | haiku | `D1 D2 D3 D4 [T] D5 D6` | correct — 551, turn 5 (confirmed twice — see below) |
| 6 | haiku | `D1 D2 D3 D4 D5 [T] D6` | correct — 551, turn 6 (after a routing mistake, see below) |
| 7 | haiku | `D1 D2 D3 D4 D5 D6 [T]` | correct — 551, turn 7 |
| 1 | sonnet | `[T] D1 D2 D3 D4 D5 D6` | correct — 551, turn 1 |
| 4 | sonnet | `D1 D2 D3 [T] D4 D5 D6` | correct — 551, turn 4 |
| 7 | sonnet | `D1 D2 D3 D4 D5 D6 [T]` | correct — 551, turn 7 |

**10/10 correct. every position from 1 to 7, both models. zero wrong answers, zero missed-then-recovered turns, zero hesitation anywhere.**

> [!note] two routing mistakes this round, both caught and fixed rather than hidden
> mid-experiment, the position-2 trial was accidentally sent a distractor (Franz Josef Land) at turn 2 instead of the target — the target went out at turn 3 instead, which quietly turned that trial into a second position-3 replicate (it agreed with the real position-3 trial: both correct at turn 3). a fresh, correctly-routed position-2 trial was launched separately and also came back correct at turn 2. the same slip happened again on position 6 (target sent at turn 5 instead of turn 6, creating a bonus position-5 replicate that also agreed with the real one), fixed the same way — a fresh, correctly-routed position-6 trial run separately, also correct. net effect: positions 3 and 5 each got confirmed twice instead of once; positions 2 and 6 needed a redo before they had a valid data point at all. no data was lost or silently discarded, just relabeled to reflect what was actually sent.

## comparison with the vault-note version

[[2026-09-01 hop-ceiling pilot - a u-curve shadow the token-ceiling test never found]] found real trouble at the middle-ish hop across two chain lengths — roughly 1-in-6 at hop 4 in a 7-hop vault-note chain, and a full unrecovered miss at hop 1 in a 13-hop chain. this wikipedia version, same protocol, same turn-by-turn amnesia design, found **none at all** — not at any of 7 positions, not with either of 2 models.

two things changed between the two tests, not one: the document source (personal notes vs. wikipedia) and the presence of closed-book screening (none before vs. required here). either could explain the difference, and this note can't separate them — a clean, screened wikipedia fact might just be an easier retrieval target than a terse personal note regardless of turn-based amnesia, or personal notes' more ambiguous/near-duplicate-prone phrasing might be the real source of the vault-note pilot's trouble, with turn count being incidental. what this result does rule out: turn-based amnesia is not a strong, universal effect that shows up on *any* material — it's at least sensitive to something about the content, and wikipedia's cleaner, unambiguous, single-fact-per-paragraph style seems to be enough to make it disappear entirely in this sample.

## related

- [[2026-09-01 hop-ceiling pilot - a u-curve shadow the token-ceiling test never found]] — the vault-note version this test is checking against a cleaner document source
- [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — the original diagnosis (exact-match shortcuts erasing position effects) this whole line of testing responds to
