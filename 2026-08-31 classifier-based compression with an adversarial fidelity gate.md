---
name: classifier-based compression with an adversarial fidelity gate
description: A two-pass compression method — classify tokens as essential vs. disposable, cut only the disposable, then have a separate agent adversarially score what survived — as a named, reusable technique distinct from rule-based word-dropping
created: 2026-08-31
aliases:
  - classifier-based compression with an adversarial fidelity gate
  - two-pass compression with a fidelity gate
tags:
  - pkm
  - ai
  - compression
  - research
  - technical
---

A compression method for text an LLM will read later, not text a human reads or text an LLM is actively reasoning through mid-task (see [[2026-08-31 research on compressing llm reasoning and notes without losing information|the research survey]] for why those are different problems with different solutions). Two passes, done by two separate agents so the compressor never grades its own homework:

1. **Classify, then cut.** One agent reads the note and tags spans as essential (facts, numbers, decisions, links, code identifiers) or disposable (connective prose, restated context, filler transitions). Only the disposable spans get cut — this is span-level judgment, not a fixed word list, so it can remove a whole clause or sentence when the *content* of that clause is disposable, not just when it matches a grammar pattern.
2. **Score, adversarially, by someone else.** A second agent, given only the original and the compressed version, gives a severity-weighted retention score (not a percentage-of-words-changed) and names every specific loss it can find. This is the gate: a compression pass with no independent fidelity check cannot be trusted to know which of its own cuts removed an argument rather than a word.

## Measured

Aggregate numbers (five real notes, two independent runs) are in [[2026-08-31 research on compressing llm reasoning and notes without losing information|the research survey]] rather than duplicated here: roughly 31-40% token cut, retention scores 85-98 out of 100, zero losses to any fact, number, code identifier, or link across every run measured so far. What breaks instead: epistemic markers, confidence hedges, and causal/provenance connectives — the argument's texture, not its content.

## Why this is a different mechanism than a rule-based word-dropper

A fixed rule list (drop articles, filler words, hedging phrases, preserve every heading and bullet exactly) can only ever remove individual words or short phrases matching a pattern — it can never decide "this whole sentence adds nothing" the way a classifier judging span-level content can. That ceiling shows up directly in measurement: the same five notes, run through a word-level rule-based compressor instead, saved under half as much (11-19% vs. 31-40%) at statistically the same fidelity — same failure mode of dropping connective texture, just distributed differently, since a fixed rule can't tell a load-bearing hedge from a disposable one and a span classifier at least has the chance to.

## Where this would actually get used

Not yet built as a skill. The candidate use case is compressing agent-read-only vault notes in place — dense reference notes and catalogs are closest to a free win (content-heavy, light connective prose, the case a classifier is built for); narrative notes carrying a chain of reasoning are the risky case, since reasoning is exactly what this method's own failure mode eats first. Any real implementation needs the adversarial gate as a built-in step, not an optional check run once during prototyping — a compressor, classifier-based or rule-based, cannot self-certify which of its own cuts were safe.

## prior art: no exact match found

A GitHub search turned up compression tools for LLM context but nothing combining classify-then-cut with a verification gate the way this method does. [marv1nnnnn/llm-min.txt](https://github.com/marv1nnnnn/llm-min.txt) distills docs into a dense format for LLM consumption but has no verification step, one-way compression only. PackRat (an auto-learning codebook compressor, cited in the HuangOwen/Awesome-LLM-Compression list) claims lossless round-trip via tiktoken, but that's syntactic codebook substitution, not semantic essential-vs-disposable judgment. A Hacker News thread on llm-min.txt independently raised the same idea — use a separate LLM to verify a compressed doc kept task-relevant fidelity — but no shipped repo implements it as a gate. This method appears to be genuinely unclaimed territory, not a rediscovery.

## Related
- [[2026-08-31 research on compressing llm reasoning and notes without losing information]]
- [[2026-08-28 agent instruction bloat - modular skills and compact synthesis]]
- [[header extraction for token-efficient retrieval]]
- [[skills/token-thrift/SKILL|token-thrift]]
