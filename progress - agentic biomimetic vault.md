---
date: 2026-08-27
created: 2026-08-27
tags:
  - progress
  - initiative
  - pkm
  - ai
  - biomimetic
status: active
goal: "Transform the PKM vault into an active biomimetic thought partner with organic memory consolidation, forgetting curves, and cognitive sparring."
aliases:
  - progress - agentic biomimetic vault
  - agentic biomimetic vault progress
  - progress agentic vault
---

# Progress: Agentic Biomimetic Vault

> **Goal:** Evolve the vault from a static repository of Markdown files into an active, biologically-inspired thought partner that consolidates memories during idle periods, prunes obsolete noise, tracks belief confidence, and challenges human assumptions through cognitive sparring.

> [!todo] next
> - **next:** Build the nightly consolidation agent that reads the day's scratchpad and git commits and writes atomic facts into `memory.md` and `profile.md`.
> - **blocked:** nothing

---

## 🟢 Current State (What Works Now)

* **Living User Profile Initialized:** Created [[profile]] (2026-08-28, commit `60971f39`) capturing technical domain, working preferences, guardrails, and linking to active progress hubs.
* **Atomic Decision Placement Defined:** Refined memory architecture—permanent architectural decisions live directly in concept/progress notes, while Git DAG serves as the immutable chronological trace (avoiding calendar log fragmentation and dual sources of truth).
* **First-Principles Architecture Defined:** Replaced over-engineered database proposals with Markdown + Git as ground truth, augmented by an active agentic consolidation layer ([[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]]).
* **3-Tier Memory Ladder:** Established explicit tiering from raw machine telemetry (Tier 1) $\rightarrow$ task solutions (Tier 2) $\rightarrow$ permanent concept notes anchored in human intent (Tier 3) ([[public/grow memory|grow memory]]).
* **7 Cognitive Sparring Lenses:** Formalized sparring tools (frame inversion, contradiction radar, pre-mortems, Occam's triage) to prevent the AI from acting as a passive agreeable mirror ([[public/2026-08-27 AI - 7 Cognitive Sparring Lenses|7 Cognitive Sparring Lenses]]).
* **Synaptic Weighting Principles:** Modeled link connectivity on biological synapses with Hebbian co-activation (LTP) and active sleep pruning (SHY) ([[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]]).

---

## 🟡 Active Experiments & Next Steps

- [ ] **Build the Nightly Consolidation Agent:** Create a scheduled background script (`cron` / daemon) that reads the day's scratchpad and git commits, extracts atomic facts into `memory.md`, and updates `profile.md`.
- [ ] **Implement Belief Confidence & Decay Tagging:** Add confidence scores (`confidence: 0.0–1.0`) and staleness timers to high-level facts in `profile.md`.
- [ ] ~~**Evaluate Local Mem0 vs Native SQLite:**~~ Deferred. [[public/2026-08-27 Mem0 memory architecture - cloud pricing, security, and local privacy|the Mem0 note]] already lands on local-first; an append-only `memory.md` tests the same idea cheaper. Revisit only if v0 extraction quality is the bottleneck.

---

## 🔴 Blockers & Open Questions

* **Trigger Logic for Proactive Surfacing:** Defining reliable heuristics for when the AI should proactively inject briefings into the daily note without becoming noisy notification spam.
* **Inhibitory Edge Traversal:** Finalizing SQLite schema for negative/inhibitory link weights (`type = 'contradicts'`) to suppress superseded notes from agent context windows.

---

## 📚 Connected Research & Tools

* **Core Architecture:** [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]], [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]]
* **Consolidation & Pruning:** [[public/grow memory|grow memory]], [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]], [[public/vault synapse pruning|vault synapse pruning]]
* **Cognitive Sparring:** [[public/2026-08-27 AI - 7 Cognitive Sparring Lenses|7 Cognitive Sparring Lenses]]
* **Longitudinal Corpora:** [[longitudinal personal journals and emotional datasets|longitudinal personal journals & emotional datasets]]
