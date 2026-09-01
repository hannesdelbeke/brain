---
name: why the u-curve disappeared in candidate 2's multi-document test
description: standalone diagnosis of why the fourth candidate-2 experiment found no lost-in-the-middle position effect at all, pulled out of the design note and the adversarial literature check into its own note
created: 2026-09-01
tags:
  - pkm
  - research
  - readability
  - llm
  - lost-in-the-middle
---

> [!summary] eli5
> the fourth candidate-2 experiment expected accuracy to dip when the answer sat in the middle of 20 documents (the classic "lost in the middle" effect). it didn't dip at all — flat 83.3% at position 1, 10, and 20. this note explains why, in one sentence: the question asked for a unique serial number, which the model can find by exact match no matter where it sits, so the test never actually stressed position-based memory.
> done, diagnosis only, no new experiment run here.
> **needs from you:** nothing, this is background for [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]].

**why:** [[2026-09-01 publish plan - readability and compression research as papers]]

## the missing ingredient

[Liu et al. 2023](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf) built their test on NaturalQuestions-Open: the gold answer is a short factual string embedded in ordinary wikipedia prose, and a real dense retriever (Contriever) pulls in genuinely topically-close distractor passages. finding that answer means doing real semantic search across a stack of similar-looking documents — there's no shortcut.

candidate 2's fourth experiment asked "why was serial X493-22 recalled" against 20 synthetic documents, with the serial number planted verbatim in exactly one of them. that's not a semantic search problem, it's a lexical grep — the model can locate the answer-bearing document by matching one unique string, regardless of where in the stack it sits. position stops mattering because the retrieval step never required position-robust reasoning in the first place.

## this isn't a guess, other 2025-2026 papers hit the same wall

[NoLiMa](https://arxiv.org/abs/2502.05167) (Adobe, ICML 2025) found frontier models pass easy needle-in-haystack tests mainly because the needle and the question share literal words — remove that overlap and even GPT-4o drops from 99.3% to 69.7% by 32K tokens.

[Facts as First-Class Objects](https://arxiv.org/html/2603.17781) (2026) found Claude Sonnet 4.5 gets 100% accuracy up to 97.5% of its context window, zero lost-in-the-middle dip, specifically when each fact is keyed by a unique lexical tuple the query can exact-match against — the identical shape as candidate 2's serial number.

meanwhile the architecture literature ([On the Emergence of Position Bias in Transformers](https://arxiv.org/abs/2502.01951), MIT ICML 2025, and its 2026 follow-up [Lost in the Middle at Birth](https://arxiv.org/html/2603.10123)) argues the u-shaped bias is baked into every causal transformer at initialization, before any training — so it isn't something a model ages out of. put together: the bias is still there, the test just handed the model a way around it.

## what this rules out

it rules out "claude/haiku has architecturally outgrown lost-in-the-middle" as the explanation — the architecture papers argue the opposite, that the bias can't be trained or scaled away. it also isn't evidence the vault's formatting-null finding (bold/chunking don't help) is wrong; that's a separate claim, checked separately in [[2026-09-01 adversarial literature check for candidate 2]], and survives.

## the fix, in one sentence

remove the exact-match shortcut: ask about a fact using different words than the source document uses, so there's no string the model can grep for, the same way Liu et al.'s paraphrased wikipedia answers forced real search. worked out in full in [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]].

## related

- [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] — the experiment this diagnosis explains
- [[2026-09-01 adversarial literature check for candidate 2]] — where this explanation was first found, in full
- [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]] — the fix, as a runnable experiment
