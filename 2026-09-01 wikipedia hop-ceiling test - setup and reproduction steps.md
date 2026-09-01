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
> the earlier hop-ceiling pilots used personal vault notes, which vary wildly in quality and length. this note runs the same kind of test on real wikipedia paragraphs instead — closer to the original lost-in-the-middle paper's own design — and adds two things the vault-note pilots didn't have: a check that the model doesn't already know the target fact from training (closed-book screening), and a second model tested side by side with haiku, so any position effect isn't just one model's quirk.
> in progress — this note is being written *as the experiment runs*, so the setup is nailed down before any result could bias how it's described.
> **needs from you:** nothing yet — check back once the result section is filled in.

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

## closed-book screening — round 2 (in progress)

**candidate fact:** Zavodovski Island (part of the Traversay Islands, South Sandwich Islands), peak elevation, sourced from [Traversay Islands](https://en.wikipedia.org/wiki/Traversay_Islands): "551 metres (1,808 feet) above sea level."

**question:** "how many metres above sea level is the highest point of Zavodovski Island?"

**screening method:** identical to round 1, both models, fresh subagents, tool-use count checked.

**result:** pending — filled in once both screens return.

## the plan once a fact clears screening

- **document pool:** the target fact plus 8 distractor paragraphs pulled from wikipedia, one paragraph each, topically unrelated to the target and to each other: [Vaquita](https://en.wikipedia.org/wiki/Vaquita), [Franz Josef Land](https://en.wikipedia.org/wiki/Franz_Josef_Land), [Tokelau](https://en.wikipedia.org/wiki/Tokelau), [Rapa Nui language](https://en.wikipedia.org/wiki/Rapa_Nui_language), [Lonesome George](https://en.wikipedia.org/wiki/Lonesome_George), [Danakil Depression](https://en.wikipedia.org/wiki/Danakil_Depression), [Möbius strip](https://en.wikipedia.org/wiki/M%C3%B6bius_strip), [Basking shark](https://en.wikipedia.org/wiki/Basking_shark) — full extracted text quoted below once the chain is finalized.
- **why more than 3 positions this time:** every prior round (both the vault-note pilots and the 13-hop chain) only ever tested 3 positions per chain (1/4/7 or 1/7/13) — enough to notice trouble exists, not enough to rule out that the specific positions picked were a coincidence. this round tests **every position in a 7-hop chain (1 through 7)**, with one model, to get an actual shape instead of 3 sampled points.
- **cross-model check:** the same chain re-run with a second model at a subset of positions, to check whether any shape found is haiku-specific or holds across models. models used are tracked explicitly per trial, not assumed.
- **protocol, unchanged from the vault-note pilots:** one fresh subagent per trial, resumed turn-by-turn via direct messages, each turn showing only that document's text plus the standing instruction (answer directly, or reply exactly "next"). no re-sent history — the only memory available to the model is whatever it carries forward itself.

## result

pending.

## related

- [[2026-09-01 hop-ceiling pilot - a u-curve shadow the token-ceiling test never found]] — the vault-note version this test is checking against a cleaner document source
- [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — the original diagnosis (exact-match shortcuts erasing position effects) this whole line of testing responds to
