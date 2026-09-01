---
name: designing a true multi-document lost-in-the-middle test for candidate 2
description: experiment design for testing markdown formatting against LLM fact-retrieval at genuine multi-document Lost-in-the-Middle scale, after three single-document nulls. now run — see the result section. a fourth null on formatting, and the base position effect itself didn't reproduce either
created: 2026-09-01
tags:
  - pkm
  - research
  - readability
  - llm
  - experiment-design
  - lost-in-the-middle
---

> design (don't run) the multi-document lost-in-the-middle experiment that candidate 2's three single-document nulls concluded was still missing — read Liu et al. 2023's actual methodology first, then specify documents, formatting variable, scale, questions, and a concrete ready-to-run plan

three single-document fact-retrieval tests (16 items/~250 words, 50 items/~700 words, 95 items/~8,100 words) all returned a clean null: flat, bold, and chunked-under-sub-headings formatting made no measurable difference to a Claude/haiku reader's accuracy, 100% in every condition. the honest conclusion each time was that one long document, however long, isn't the shape [Lost in the Middle](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf) (Liu et al. 2023, arXiv:2307.03172) actually tested — a haiku-sized model holds one document in context without strain regardless of decoration. this note designs the real version: several separate documents concatenated into one context, the paper's own shape, not attempted yet.

## what liu et al. 2023 actually tested

multi-document QA on NaturalQuestions-Open: 2,655 queries whose gold answer is a paragraph, answered against Wikipedia passage chunks of at most 100 tokens each. exactly one retrieved passage per query contains the answer; the rest are distractors pulled by Contriever (fine-tuned on MS-MARCO) — real passages, topically close, genuinely wrong.

context size was varied in three steps: 10, 20, and 30 total documents, averaging 1,476 / 2,946 / 4,419 tokens respectively (GPT-3.5/Claude tokenizer). the answer document's position was swept explicitly rather than left to chance — for 20 documents the tested indices were 0, 4, 9, 14, 19 (position 1, 5, 10, 15, 20); 10 documents used 0, 4, 9; 30 documents used 0, 4, 9, 14, 19, 24, 29. distractors were ordered by decreasing relevance, the way a search engine would present them.

the model received the question plus all k documents and was asked to answer using only the provided passages; accuracy was scored as whether any gold answer string appeared in the output. closed-book (no documents) and oracle (only the correct document) runs served as baselines. models tested included GPT-3.5-Turbo (4K/16K), Claude-1.3 (8K/100K), MPT-30B-Instruct, LongChat-13B, and a GPT-4 spot-check on 20 documents.

the finding candidate 2 is chasing: accuracy traces a U-curve against answer position — high near the start and end of the context, degraded in the middle, sometimes below closed-book. this only shows up because the context is built from several genuinely separate documents with one clear answer-bearer among distractors; none of candidate 2's three single-document pilots had that shape.

## the formatting variable: delimit documents, don't restyle their insides

candidate 2's original variable was list-item formatting (flat / bold-per-item / chunked-under-sub-headings) inside one document. translating that to a multi-document context, two options exist.

**(a) reformat each document's own internal structure**, keeping document count and order fixed. rejected — this is the same variable the three single-document pilots already tested to death, just repeated once per document in a longer context instead of once per experiment. it wouldn't test anything the nulls haven't already covered, and it doesn't touch the part of Liu et al.'s setup that actually produces the U-curve, which is cross-document position, not within-document layout.

**(b) format how documents are delimited from each other** — a plain blank line between them, a bolded one-line document title, or a numbered `### Document N` markdown header. adopted. this is the faithful translation: "chunking helps" at list-item granularity becomes "can the model tell where one document ends and the next begins, and jump straight to the right one" at multi-document granularity. it also sits directly on top of the mechanism Liu et al. found — if headers or bold titles make the answer-bearing document easier to locate regardless of its position, that would show up as a flatter position curve under chunked formatting than under flat formatting. that is a real, checkable hypothesis; restyling text inside a document that's already easy to find is not.

three conditions, applied only to the separators:
- **flat** — documents separated by a blank line only, no visible boundary marker
- **bold** — each document opens with a bolded one-line title, `**Document 7 — Coastal Ridge Recall Notice**`
- **chunked** — each document opens with `### Document 7` plus a one-line synopsis underneath, mirroring the sub-heading condition from the single-document pilots

## scale

Liu et al. found the degradation at 10-20 documents and it was still present, more pronounced, at 30. the primary design here targets 20 documents per context — the upper edge of where they already demonstrated the effect — each document roughly 200 words (~270 tokens) of synthetic prose, giving a per-context content size of about 4,000 words (~5,400 tokens), comparable to or above Liu et al.'s own 20-document average of 2,946 tokens once delimiter overhead is added. this is deliberately richer per document than their 100-token Wikipedia stubs, since a document needs enough body for a delimiter style to have anything to visually set off — a one-line stub can't meaningfully look "chunked."

position is swept at three points rather than their denser five-to-seven-point index sweep: 1 (start), 10 (middle), 20 (end). this is a deliberate coarsening for cost, named here rather than silently substituted — it's still an actual start/middle/end sweep, which is the part of the design the single-document pilots never had at all.

each document follows the same synthetic-recall-notice shape the earlier pilots used (fictional products, serials, and one of six reason clusters — battery, valve, strap, sensor, hinge, coating — so the model can't answer from prior knowledge and can't shortcut on a bare keyword, since 2-4 other documents share the same reason cluster as near-duplicates). one document per context is the answer-bearer; the other 19 are same-domain distractors, playing the role Contriever's retrieved-but-wrong passages played in the original paper.

## question design: retrieval first, synthesis as a stretch arm

primary measure: single-document retrieval questions, the same shape as all three prior pilots and the same shape Liu et al. scored — "what reason was given for serial X493-22," answerable from exactly one document, scored by exact/substring match against a stored answer key. three differently-worded questions per trial, all targeting the same answer-bearing document, to damp single-question noise without regenerating content.

secondary, optional stretch arm: one cross-document synthesis question per trial requiring the target fact plus a fact from a second, fixed-position distractor document (for example, comparing the severity of two named reasons). this is closer to genuinely stressing "lost in the middle" — a model that can locate document A but not document B, or locates both but combines them wrong, fails this question for reasons the retrieval-only metric can't distinguish. score it separately from the primary accuracy number rather than folding it in, since a wrong answer here is a confound (which document failed, or was the combination wrong) that the paper's own single-document-answer metric was built to avoid.

## cost and feasibility

content generation and delimiter formatting are split into two different costs on purpose. the three formatting variants of a given position/instance share the same underlying 20 documents and only differ in the separator text — that's a pure string-templating step, not something worth an LLM call (ponytail: this is rung 6 of the ladder, not rung 7). so each (position × instance) cell is generated once by an LLM call, then expanded into its three formatted variants by a script.

primary design: 3 positions × 2 independent content instances = 6 generation calls, each producing 20 documents (~5,400 tokens output). each generation expands into 3 formatted contexts = 18 total trial files. each trial gets one fresh, blind Claude/haiku subagent call — given only the formatted context and the question list, never told formatting is the variable — answering 3-4 questions. 18 answering calls at roughly 5,700 input tokens (the context) plus a few hundred output tokens each.

**total: 24 agent calls, roughly 140K tokens end to end** (≈32K generation + ≈108K answering). that is smaller than the third single-document pilot already run in this session (6 documents × ~8,100 words was itself around 65K tokens of content alone, before grading calls), while testing a categorically different and harder condition. trivially executable with Claude/haiku subagents in one sitting, batchable as 6 generation calls followed by 18 answering calls, both batches parallelizable.

full-scale alternative, closer to matching Liu et al.'s own largest setting (30 documents) and denser position sweep (5 points: 1, 8, 15, 23, 30): 10 generation calls, 30 trial contexts, 30 answering calls, 40 calls total, roughly 372K tokens (≈89K generation + ≈283K answering). still one-sitting feasible on haiku, at about 2.6x the token cost and 1.7x the call count of the primary design. the recommendation is to run the primary (20-doc, 3-position) design first — it's a real start/middle/end sweep at genuine Liu-et-al scale, which is the part missing so far — and only pay for the fuller sweep if that run shows any position or formatting signal worth resolving further.

## the ready-to-run plan

a future agent (or this one, later) can execute this directly:

1. `candidate2-multidoc/generate_content_prompt.md` — one parameterized prompt (instance seed, target position, the six reason clusters) for the content-generation calls. run it 6 times (3 positions × 2 instances), saving each result as `candidate2-multidoc/content/{instance}_{position}.json`: 20 documents (title, serial, reason-cluster, body text), which index is the answer-bearer, and the ground-truth answer strings for the primary and stretch questions.
2. `candidate2-multidoc/format_delimiters.py` — a small pure-python script, no LLM call, that reads one content JSON and a condition name (`flat`/`bold`/`chunked`) and emits one concatenated markdown context file with that condition's document separators applied. run it 3 times per content file (18 files total) into `candidate2-multidoc/contexts/{instance}_{position}_{condition}.md`, each paired with a `{...}_questions.md` holding the 3-4 questions and nothing that names the formatting variable.
3. dispatch 18 fresh Claude/haiku subagent calls, one per context file, each given only the file path and its question file, told to answer from the document and nothing else. collect answers into `candidate2-multidoc/results.json`.
4. grade by exact/substring match against `candidate2-multidoc/content/*.json`'s answer keys, same convention as the three prior pilots and as Liu et al.'s own scoring. tabulate accuracy by condition × position (a 3×3 table for the primary design) — a flat table means another null; a curve that dips in the middle, and dips less under chunked/bold than flat, would be the first actual signal this line of research has found.

## result

ran the primary design exactly as specified above: 6 content generations (3 positions x 2 instances), each expanded into 3 formatted contexts (18 total), each answered blind by a fresh claude/haiku subagent on 3 questions. 54 graded question-answers.

overall accuracy: 45/54, 83.3%. this is the first non-ceiling result in this research line. all three single-document pilots landed at 100%.

### accuracy by position x condition

| position | flat | bold | chunked |
|---|---|---|---|
| 1 | 100% | 100% | 50% |
| 10 | 83.3% | 83.3% | 83.3% |
| 20 | 83.3% | 83.3% | 83.3% |

### the base position effect did not reproduce

position marginals, averaged across the three formatting conditions: position 1 is 83.3%, position 10 is 83.3%, position 20 is 83.3%. identical.

there is no u-curve. [liu et al.'s](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf) core finding was degraded accuracy for a mid-context answer document. this design still didn't produce that, even at 20 documents, even with a genuine multi-document context, the shape the three single-document pilots were missing. that's the bigger finding here, separate from formatting: this setup, at this scale, on claude/haiku, doesn't reproduce the paper's own base effect. any read of the formatting numbers below has to sit on top of that fact, not next to it.

### the formatting comparison

condition marginals, averaged across the three positions: flat 88.9%, bold 88.9%, chunked 72.2%.

chunked looks worse, but the gap comes from one cell. both content instances at position 1 lost accuracy specifically under chunked delimiters, on document sets where flat and bold — identical underlying content, only the separator differs — scored perfectly. at position 10 and position 20, all three conditions tied at 83.3%.

n=2 instances per cell. one cell moving is not enough to call this a real formatting effect over noise. a bigger instance count at position 1 specifically would be the next thing to check, if this line of research continues.

### where the errors actually came from

- 8 of the 9 wrong answers were on the same question wording, "why was serial X recalled?" — the other two phrasings of the same question, same document, mostly succeeded. that's a question-phrasing effect, not a position or format effect.
- one full content instance (position 10, instance 2) missed that question in all three formats. the model consistently pulled the reason from a different document in the same near-duplicate reason cluster, not the target. that's the near-duplicate-cluster design working as intended — a real confusion, driven by content, not by where the document sat in context or how it was delimited.

### conclusion

no evidence formatting helps or hurts multi-document retrieval at this scale, past one thin, unreplicated signal (chunked at position 1) too small to trust on its own.

no evidence of the u-curve either, and that's the more important miss. this design still doesn't reproduce liu et al.'s own base position effect at 20 documents on claude/haiku, so the formatting comparison sits on ground that isn't behaving like the paper it's modeled on. the honest read is a fourth null on the formatting question, plus a separate, newly-found null on the position effect itself — both belong in any writeup, and neither should get buried under the other.

### a hypothesis for why, not just that it didn't reproduce

liu et al.'s original models — GPT-3.5-Turbo, Claude-1.3, MPT-30B-Instruct, LongChat-13B — are all 2023-era. claude/haiku is a later-generation small model, and a large 2026 study already cited elsewhere in this research ([Structured Context Engineering for File-Native Agentic Systems](https://arxiv.org/html/2602.06384v1), 9,649 experiments across 11 models) found no statistically significant aggregate formatting difference on frontier-era models specifically, consistent with position/formatting sensitivity shrinking as models improve. this experiment's null u-curve reads as the same trend showing up one level down: not just "frontier models stopped caring about formatting," but "a modern small model may have stopped exhibiting the base lost-in-the-middle degradation at all," at least at this document count and length. untested here: whether a bigger sweep (liu et al.'s full 30-document, denser position setting) reproduces the u-curve on haiku, or whether the effect is genuinely gone at this model generation regardless of scale — that would need the full-scale alternative named in the cost section above, run specifically to test the u-curve's presence rather than the formatting question.

## related

- [[2026-08-30 agent reading versus human reading, which formatting rules transfer]] — the mechanism argument this whole line of testing is trying to check empirically
- [[2026-08-30 readability and reading-speed research applied to note-taking vaults]] — the human-reading research the agent-side claims are contrasted against
- [[2026-09-01 process log - from readability question to publish plan]] — how the three single-document pilots and this gap were found
