---
tags:
- ai
- reasoning
- test-time-compute
- local-llm
- architecture
aliases:
- test-time compute vs model size
- self-questioning small models
- fast reasoning vs slow single-shot
---

Why compact, high-speed LLMs with self-reflection and test-time reasoning frequently outperform larger monolithic models on logic, debugging, and code generation.

Related: [[local LLM generation speed vs human reading speed]], [[popular AI models landscape]], [[model weights vs vector embeddings vs map-reduce]]

## The self-correction advantage

Standard monolithic LLMs predict text strictly sequentially. If an unverified assumption or logic bug is emitted early in generation, a single-shot model cannot backtrack and builds all subsequent output on top of that flaw.

In contrast, models that question themselves (using chain-of-thought verification, test-time compute, or draft-and-critique loops):

- **Catch edge cases before final output:** The model reviews intermediate code, spots runtime hazards (e.g. unhandled nulls, boundary conditions), and revises its implementation before presenting the answer.
- **Explore solution spaces:** Generating multiple fast candidate hypotheses and picking the most coherent result (best-of-N sampling) yields higher code pass rates than one slow generation.
- **Reduce confident hallucinations:** Interrogating internal contradictions prevents premature commitment to incorrect claims.

## The token throughput trade-off on edge hardware

On memory-bandwidth-constrained devices (such as laptop CPUs):

- **Monolithic 70B model (1–2 tok/sec):** Spending 300 tokens on a single-shot response takes minutes and risks uncorrected logic flaws.
- **Compact 3B model (25–35 tok/sec):** Can generate 200 tokens of internal reasoning, critique its own draft, and deliver a verified final response in under 10 seconds.

## Reasoning vs parametric knowledge boundaries

Self-questioning fundamentally enhances reasoning ability, but cannot synthesize missing parametric facts:

- **Where self-questioning small models win:** Logic puzzles, algorithmic debugging, syntax translation, multi-step planning, and error recovery.
- **Where large monolithic models still dominate:** Deep factual recall, obscure API memorization, niche domain libraries, and broad world knowledge.

## The optimal local architecture

The highest-performing local setup pairs a fast, lightweight reasoning model with deterministic external retrieval:

- **External search & RAG (`rg` / SQLite FTS5 / Web search):** Injects exact, fresh facts into context.
- **Lightweight self-reflecting LLM (3B–7B):** Provides fast, verified reasoning over the retrieved data without latency bottlenecks.
