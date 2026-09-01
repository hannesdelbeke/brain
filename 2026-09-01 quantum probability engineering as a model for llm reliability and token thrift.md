---
name: quantum probability engineering as a model for llm reliability and token thrift
description: quantum computing never promised a single-run correct answer either, only a bounded-error distribution shrinkable by spending more measurements; the same shot-budget-vs-confidence math appears independently in llm self-consistency, semantic entropy, and conformal prediction, and the adaptive-shot-allocation line of quantum optimizers is the same technique as adaptive-consistency sampling for llms
created: 2026-09-01
tags:
  - ai
  - quantum-computing
  - reliability
  - uncertainty
  - token-thrift
---

> write a note comparing quantum research with ai, since quantum relies on probability, people say ai can't be trusted for the same reason (non-deterministic, might hallucinate), find papers, see which angles compare, and find new links relevant to using ai more reliably or efficiently, e.g. token thrift

## the objection and the reply

"ai can't be trusted, it's not deterministic, same prompt gives a different answer, sometimes a hallucination" is true of llm sampling.

it is also true, by design, of every quantum algorithm ever built: a circuit run once gives one bitstring, not "the answer", the same way one llm decode gives one completion, not "the answer".

quantum computing never promised a single correct run, it promises a distribution with a bounded error probability, plus 40 years of formal tools for shrinking that error to any target by spending more measurements, and a lot of that machinery maps directly onto llm reliability engineering.

## the parallel, concept by concept

**shots**, running a circuit N times to build a distribution, is the same move as **self-consistency**, [sampling an llm N times and taking the majority answer](https://arxiv.org/abs/2203.11171) — repeated independent draws plus aggregation suppress per-draw noise in both.

**shot noise** falls as 1/√N in quantum measurement, and diminishing accuracy return per extra self-consistency sample follows the same curve on the llm side, so past some point more samples buy little in either field.

**adaptive shot allocation** in variational quantum algorithms — [iCANS](https://arxiv.org/abs/1909.09083) and its successor [gCANS](https://arxiv.org/abs/2108.10434) — spend few shots when an estimate is easy and more when it's ambiguous, stopping once a precision target is hit, and [adaptive-consistency for llms](https://arxiv.org/abs/2305.11860) is the identical idea: stop sampling once a confidence threshold is met instead of always drawing a fixed N, cutting sample budget up to 7.9x for under 0.1% accuracy loss. these were arrived at independently, six years apart, in unrelated fields, which is the strongest single finding in this note.

the **threshold theorem** behind quantum error-correcting codes — below a physical error rate, adding redundancy drives logical error toward zero — is the same shape as ensembling, verifier chains, or multi-agent cross-checks reducing an effective hallucination rate: redundancy plus a decoding rule converts a noisy channel into an arbitrarily reliable one, at a resource cost.

von neumann entropy measures how mixed a quantum state is, and [semantic entropy](https://www.nature.com/articles/s41586-024-07421-0) does the equivalent for an llm: sample N completions, cluster by meaning rather than exact text, take entropy over the meaning-clusters, and a high value flags a likely hallucination. entropy over an ensemble is the honest measure of "how sure is this system", not the confidence of any single draw.

a quantum confidence interval states a coverage guarantee, and [conformal language modeling](https://arxiv.org/abs/2306.10193) does the same for llms: a calibrated stopping and rejection rule that returns an output *set* guaranteed to contain a correct answer with probability at least 1−α, turning "the model says X" into "X is in a set that's right (1−α) of the time".

## where the analogy breaks

quantum error rates come from well-characterized physical noise models with known statistics, where llm error rates are task-dependent, non-stationary, and not drawn from any known distribution, so the 1/√N shot-noise law is a much cleaner guarantee than the empirical accuracy-vs-N curve on the llm side.

repeated quantum shots are close to i.i.d. draws from a fixed state, but repeated llm samples at temperature above zero draw from a learned distribution that can itself be systematically wrong, confidently and consistently, on a class of inputs, and no amount of resampling fixes a biased distribution, only a noisy one — self-consistency helps the high-entropy case (the model doesn't know), not the low-entropy case (the model is sure and sure wrong).

papers that borrow quantum vocabulary directly for llms — [semantic wave functions](https://www.opastpublishers.com/open-access-articles/semantic-wave-functions-exploring-meaning-in-large-language-models-through-quantum-formalism-9029.html), quantum-measurement-as-dropout training proposals — read as speculative framing or genuine quantum-hardware research, not evidence that llms are secretly quantum systems. the load-bearing part of this comparison is provider-agnostic statistics of noisy-repeated-measurement-plus-aggregation, not a physical claim.

## where this pays for itself: token thrift

skip fixed "always sample 5, take majority" self-consistency, and use a stopping rule instead, per adaptive-consistency's beta or entropy-based criterion, so easy queries stop at one or two samples and only ambiguous ones spend the full budget.

semantic entropy over a small sample, three to five completions clustered by meaning, is a cheap pre-flight uncertainty check: route high-entropy queries to a bigger model, a verifier pass, or a human, and let low-entropy queries through on the cheap path, which is a concrete gate on when to spend more tokens rather than static routing by prompt length or task type.

conformal-style calibration, holding out a small labeled set and picking a threshold for a target coverage guarantee, turns "we think this stopping rule is safe" into a defensible number, and makes the token-vs-reliability trade-off explicit instead of a guess.

this connects to [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]]'s finding that llm-as-judge scoring is volatile run to run and that the field's own fix is the same one, run the judge multiple times and aggregate by majority vote rather than trusting one greedy call, so both notes land on the same design rule from two different starting angles.

## related

- [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]] — the same repeat-and-aggregate fix, arrived at from a compression-pipeline reliability question rather than a quantum one
