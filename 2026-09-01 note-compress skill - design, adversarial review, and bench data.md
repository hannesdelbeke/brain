---
name: note-compress skill - design, adversarial review, and bench data
description: Final design decision for the note-compress skill, the adversarial case for and against it, and real measured bench numbers on this vault's own notes
created: 2026-09-01
tags:
  - pkm
  - ai
  - compression
  - research
  - technical
---

> [!warning] don't run this routinely
> real bench data below: 0.5% mean cut across this vault's actual eligible notes. [[header extraction for token-efficient retrieval|header extraction]] stays the default lever. Use this by hand, occasionally, only on a long prose-heavy note unlikely to be a MOC or diagram-heavy — see the conclusion section at the bottom.

[[skills/note-compress/SKILL|note-compress]] is a working skill, not another proposal: one LLM call per note, gated by a free mechanical fidelity check, targeting only notes likely to be reread enough to pay for the call. This note is the design rationale, the adversarial case for and against it, and the real bench numbers behind it.

## the design

Two independent reviews argued for and against the two-pass classify-then-adversarially-score design [[2026-08-31 classifier-based compression with an adversarial fidelity gate|measured earlier]] (31-40% cut, 85-98/100 retention, but a paid model call for the fidelity check itself, not just the compression). Both converged on the same alternative: one LLM call, not two, plus a free mechanical fidelity gate.

The justification is empirical. Across every compression measured against this vault's real notes, across both sessions, the only failure class that ever occurred was framing drift — a hedge softened, a causal connector dropped. Never a lost fact, number, wikilink, or code identifier. A program can catch the second class for free by extracting wikilinks, URLs, dates, numbers, and code spans from the original and the compressed text and checking nothing essential is missing (a subset check, not equality — repeating a fact isn't a loss, dropping one is). It cannot judge the first without paying for another model call. So the skill spends its one call on the compression itself, and gets the fidelity check for free.

The break-even math the two reviews ran landed differently depending on pricing and design assumptions — roughly 2 to 48 future rereads to recoup one compression call's cost — but agreed on the shape of the answer: not every note is reread enough to justify the call. [Token Reduction Is Not Cost Reduction](https://arxiv.org/abs/2607.12161) and a related pre-registered trial make the same point from the output side: a shorter input can raise total cost if it grows output length, forces a re-read, or invalidates a prompt-caching discount the original was already getting. (arXiv ID corrected — 2509.04202 is an unrelated social-event-detection paper) So the skill filters eligibility instead of compressing everything: at least 300 words, and either under a `learnings/`-style folder or above a minimum inbound-wikilink count — reusing this vault's own wikilink graph as a free reread-frequency proxy rather than tracking anything new.

## bench data

Five notes were compressed by hand first, using the exact prompt the script uses, before the live API path existed — this isolates whether the fidelity gate itself is correct from anything API-specific:

| note | words before → after | cut | gate |
| :--- | :--- | :--- | :--- |
| vector search obsoletes empty stub wikilinks | 673 → 637 | 5.3% | pass |
| pkm-search | 601 → 579 | 3.7% | pass |
| progress - local-first search daemon and indexer | 2,637 → 2,384 | 9.6% | pass |
| 2026-08-31 recency-proximity reranking prior tested against real wikilinks | 2,378 → 2,177 | 8.5% | pass |
| 2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution | 4,555 → 4,228 | 7.2% | pass |

All five passed with zero losses. The cut is far more conservative than [[2026-08-31 classifier-based compression with an adversarial fidelity gate|the standalone classifier method's]] measured 31-40% — this prompt's hard rules explicitly protect hedges and causal connectors that the earlier, narrower classifier prompt was free to cut. Lower cut for lower risk was the intended trade, and the gate confirms it held.

Against the live corpus (151 eligible notes in this vault at default thresholds), two live dry runs told a very different story than the five hand-picked notes above:

- **8-note sample:** 0 compressed, 4 rejected (all real losses — wikilinks, dates, code spans), 4 errored (the reasoning-budget bug, since fixed).
- **20-note sample, after the reasoning-budget fix:** 10 passed the gate, 8 rejected (again all real losses), 2 transient errors (both reproduced fine on a manual retry — model flakiness, not a bug). **Mean cut on the 10 that passed: 0.5%.** Four of those ten were 0.0% cut — the model returned the note back effectively unchanged rather than find anything safe to remove.

That 0.5% number is the headline finding, and it's a bad one for the skill as configured: on this vault's actual eligible-note population, the fidelity gate is doing its job, but the population it's being asked to compress is mostly not compressible under this prompt's hard rules. See below for why.

## real-world issues found only by running this against actual data

None of these showed up in the five hand-picked bench notes above. All five surfaced only once the live API and the real, unfiltered eligible-note corpus were involved: a technique that's correct in isolation breaks against real scale or real data, not against more isolated testing of the same technique alone.

- **Passing the gate doesn't mean the compression was worth running.** The headline live number: of 20 real eligible notes, 10 passed the fidelity gate, and those 10 averaged 0.5% cut — four were 0.0%. The gate is only checking "did this lose anything essential," not "was this worth a call." A note that's already tight, or where the model played it safe rather than risk a wikilink, still counts as a pass. This is the gap neither of the adversarial reviews caught, because both reasoned from the break-even math (rereads needed to justify a call) assuming the call would actually produce a real cut — not from what actually happens when a strict fidelity prompt meets a real, already-fairly-tight note.
- **The model sometimes returns empty output.** `openai/gpt-oss-20b` is a reasoning model with a hidden `reasoning` field separate from the `content` field a caller actually wants. On the same note and prompt, one call returned empty `content` while a second, otherwise-identical call returned real compressed text — non-deterministic, not tied to any specific note. Fixed by treating empty content as a retryable failure, the same as a rate limit, rather than returning it as a real result.
- **Longer notes hit the token budget before writing any content at all.** On one note, the model's hidden reasoning alone consumed the entire completion budget and returned `finish_reason: length` with zero content — a hard failure a retry alone cannot fix, since the same input would hit the same wall again. Fixed with a larger `max_tokens` and `reasoning_effort: low` to cut how much the model reasons before answering.
- **Deprecated model name.** The originally assumed Groq model, `llama-3.3-70b-versatile`, no longer exists (`404`). Caught immediately by a live smoke test, not by any static check — a reminder that a hosted-model default is a moving target, not a fact to assume from documentation or a prior session.
- **Link-dense notes are exactly the case this prompt handles worst, and exactly the case the eligibility filter is most likely to select.** The four live rejections were all notes where the model summarized instead of compressed, dropping wikilinks, dates, and inline code along the way — one lost 4 wikilinks and every number in three dates; another, at a 70.9% cut, lost 9 wikilinks, a date, and 7 code spans. These are MOC/index-style notes: high backlink count (which makes them eligible), but mostly links rather than prose (which this compression approach is bad at cutting safely). The eligibility filter as written doesn't distinguish a link-dense index note from a prose-heavy reference note with the same backlink count — it should, and doesn't yet. This is the one open gap: a wikilink-density exclusion (route link-dense notes to [[header extraction for token-efficient retrieval|header extraction]] instead, which has zero rewrite risk) would need to ship before `--apply` is safe to run unattended across a whole folder rather than one note at a time with a dry run checked first.

The fidelity gate did exactly its job in every one of these four cases: it rejected all four and left the original files untouched. The bug was never in what got written — it was in what the eligibility filter offered up to compress in the first place.

## follow-up: emoji-heavy AI-generated notes, and where relaxing the rules broke

One of the live-rejected notes, `2026-08-27 AI - 7 Cognitive Sparring Lenses.md`, is heavy with decorative emoji in every heading and stylized roleplay quote-blocks ("The Buddy Intervention: ..."). That's a distinct problem from prose bulk — a fixed hard rule ("keep every heading exactly as written") makes the decoration itself un-cuttable, no matter how the classify-and-cut instruction is worded.

Three things were tried against this exact note, live, to see if relaxing the hard rules could recover a real, safe cut:

- **Relaxing the prompt to let the model flatten roleplay framing and strip heading emoji itself:** worked on this one note in isolation (13.4% cut, clean gate pass, all worked examples preserved) once the instruction was made specific enough to forbid summarizing an example down to its caption. But regression-tested against the five originally-clean bench notes, it **mangled ASCII-art fenced code diagrams in two of them** — rewriting a box-drawing diagram into a bulleted list, violating the same "byte-for-byte, no exceptions" rule the prompt stated twice, once in emphatic all-caps. Rejected: a rule that only holds on notes without diagrams isn't safe as a shipped default.
- **Isolating just the "collapse near-synonym adjectives" instruction** ("hyper-agreeable, polite, and eager to please" → "agreeable and pleasing"), without the roleplay/heading permission: no meaningfully increased regression risk in a direct comparison — folded into the shipped `COMPRESS_PROMPT`.
- **Doing the emoji-heading cleanup mechanically instead of asking the model:** a regex scoped to heading/bullet lines, skipping fenced code blocks entirely, can't make the mistake an LLM made twice. Shipped as `delint()`, an unconditional free pre-pass before the one paid call. Delint alone doesn't rescue this specific note to a clean gate pass — a follow-up test on the delinted body still lost one number (down from 4 wikilinks + 3 dates + 5 numbers on the raw original) — because the note's worked examples each carry their own dense numeric content, the same "narrative/example-dense" case the original classifier research already named as the hardest one.

**A finding this stress-test surfaced independent of any of the above:** the exact same unmodified shipped prompt, run twice against the identical note, passed once and mangled a fenced ASCII diagram the other time — non-deterministic, not tied to any wording change tried. This is the mechanical fidelity gate's actual justification, restated more strongly than the original design rationale could without having watched it happen: no prompt wording, however carefully worded, made this model's fenced-code handling 100% reliable, so the free mechanical check is the only thing standing between "usually fine" and a silently corrupted note.

Also hit live: a verbose relaxed-prompt variant plus a long note exceeded Groq's 8,000 tokens-per-minute limit for `openai/gpt-oss-20b` on the free tier (`413`, request too large) — a real ceiling worth knowing about before assuming every note in a folder can run back-to-back without backoff.

## negative result: a cheap pre-check can't predict which notes are worth attempting

Since the mechanical gate makes every attempt structurally safe (nothing is ever written unless it verifiably preserves every wikilink/date/number/code span — the only possible failure is a wasted call, never a corrupted note), the open question isn't "is it safe to try" but "is it worth trying." Wikilink density and number density (both free, computed before spending any call) looked like plausible predictors, since the live rejections skewed toward link-dense notes.

Calibrated against all 17 real outcomes from today's live runs (8-note and 20-note samples plus the five hand-run notes), neither metric separates passes from rejects:

| | wikilinks per 100 words |
| :--- | :--- |
| rejected notes | ranged 0.21 - 3.19 |
| passed notes | ranged 0.04 - 4.02, fully overlapping |

`Obsidian improvements.md`, the highest-link-density note tested (4.02), passed with a real 3.2% cut. `2026-08-27 what already exists, prior art for a local hybrid search engine.md`, near the lowest (0.21), was rejected. Number density showed the same overlap. The working theory from the section above — link-dense notes are the risk — held for the two most dramatic individual cases (`Priority heatmap.md`, `wikilink temporal integrity.md`) but isn't a general rule once checked against the full set.

Part of why a static predictor can't fully work: the same note and the same unmodified prompt produced a pass on one call and a fenced-code failure on another (noted above) — some of the outcome is decided at call time, not by anything measurable in the text beforehand. Conclusion: don't build a pre-filter. The eligibility filter (word count + backlinks) already bounds how many notes get tried; the free gate already bounds the damage of each individual attempt to zero. Predicting per-note success in advance would spend engineering effort removing a cost — one wasted free-tier API call — that's already effectively zero.

## compared to hierarchical rollup

A hierarchical map-reduce rollup — batch-synthesizing many notes into cached monthly/tag/cluster summaries — was measured and rejected separately at this vault's current size: roughly 3,228 notes serialize to about 180k tokens of metadata, which already fits one model call, so there's no intermediate level to insert yet.

The two aren't really competing levers, the same way header extraction and note-compress weren't: rollup would operate on the whole corpus as a rebuildable cache (a read-path lever, nothing in any note ever changes), where note-compress permanently rewrites one note's body (a one-time cost, paid once, recouped only if that specific note gets reread enough). Rollup is worth building once the corpus stops fitting a single context call — roughly 5x this vault's current size, by the earlier estimate. Below that threshold, a rollup would be synthesizing a summary of something an agent could already read directly in one call, which is pure overhead with no read-cost saved. Note-compress's bar is different and per-note: worth running only on a specific note that's dense prose (not link-dense, not diagram-heavy, not worked-example-dense per the finding above) and reread often enough — which, per today's real bench numbers, is a narrower slice of this vault's actual notes than the original research hoped.

## conclusion: how to actually use this

Don't run it routinely or in bulk. The real bench numbers above say 0.5% mean cut across this vault's actual eligible notes — not worth the habit, the API calls, or the trust cost of unattended `--apply` across a folder.

Header extraction stays the everyday lever. Already shipped, 77.5% reduction, zero rewrite risk, needs nothing further. That's still the default answer to "how do I save tokens reading this vault," unchanged by anything measured here.

Use `note-compress` by hand, occasionally, only on the narrow case it's actually good at: a long, prose-heavy reference or narrative note — not a MOC, not full of ASCII-art diagrams, not stacked with numeric worked examples — that's expected to be reread by agents often. When that case comes up:

```
python skills/note-compress/compress_notes.py --dry-run --folder "<that note's folder>"
```

check the diff, then `--apply` if it looks right. One note at a time, by choice, never scheduled or automatic.

Don't build a predictor. Confirmed above that it wouldn't help, and the gate already makes every individual attempt free to fail.

One standalone win still on the table: `delint()`'s emoji-strip is free and zero-risk independent of whether the paid compression call is worth running. It currently only fires as a silent pre-step inside the compression pipeline. Exposing it as its own `--delint-only` flag, so it can run broadly across the vault with no LLM cost or gate risk at all, is a small, low-priority follow-up if the emoji-cleanup effect turns out to be wanted on its own.

## related
- [[2026-08-31 research on compressing llm reasoning and notes without losing information]] — the research survey, external literature, and why this design was chosen over the alternatives
- [[2026-08-31 classifier-based compression with an adversarial fidelity gate]] — the two-pass method this skill deliberately simplifies to one call
- [[skills/note-compress/SKILL|note-compress]] — the skill itself
- [[header extraction for token-efficient retrieval]] — the safer lever this vault already ships, and where link-dense notes should route instead
