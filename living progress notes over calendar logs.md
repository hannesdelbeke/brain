---
date: 2026-08-27
created: 2026-08-27
tags:
  - pkm
  - workflow
  - architecture
  - productivity
  - goals
  - ai
aliases:
  - living progress notes over calendar logs
  - progress notes
  - living progress notes
  - goal-driven initiative tracking
  - evolving progress notes
---

# Living Progress Notes: Goal-Driven Initiatives Over Ephemeral Daily Logs

Why personal knowledge management (PKM) and AI agents should organize active work around **Living Progress Notes** rather than fragmented calendar logs—evolving persistent initiative hubs in-place while relying on **Git history** for chronological provenance.

Related: [[public/grow memory|grow memory]], [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]], [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]], [[public/2026-08-27 agentic pkm action plan|agentic pkm action plan]]

---

## 🚫 The Problem with Pure Daily Logs

The default PKM habit is writing chronological daily notes (`day 2026-08-27.md`). While daily notes are useful as temporary scratchpads for in-flight thoughts, using them as the primary store of work creates severe systemic failure modes:

1. **Fragmentation Across 365 Files:** Progress on a single initiative (e.g. *"Build local-first search daemon"*) gets scattered across dozens of daily notes over 6 months. To understand current status, a human or AI agent must search and reconstruct history from 40 different dates.
2. **Context Window Waste for AI Agents:** When an AI assistant helps you with an active project, passing 15 daily logs forces the LLM to process thousands of irrelevant tokens (yesterday's lunch, unrelated bugs, completed errands) just to find current project state.
3. **Calendar Bias Over Problem Structure:** Progress on complex goals is non-linear. What matters is the **current frontier, active blockers, and verified architecture**, not whether an experiment happened on a Tuesday or a Thursday.

```
CHRONOLOGICAL FRAGMENTATION (Daily Logs):
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Day Aug 12  │   │  Day Aug 18  │   │  Day Aug 26  │
│  • Ran nRF   │   │  • Wrote py  │   │  • Fixed bug │
│  • Ate pasta │   │  • Shoulder  │   │  • Coffee    │
└──────────────┘   └──────────────┘   └──────────────┘
  ❌ Result: High search friction, scattered context.

LIVING PROGRESS NOTE (Initiative Hub):
┌─────────────────────────────────────────────────────────────┐
│ 📄 `progress - local-first search daemon.md`                │
│ • Goal & Desired Outcome                                    │
│ • Current Working State & Architecture                      │
│ • Active Blockers & Next Actions                            │
│ • Links to Research Notes & Executable Skills               │
└─────────────────────────────────────────────────────────────┘
  ✅ Result: Instant agent context, continuous clarity.
```

---

## 🧭 The Progress Note Architecture

A **Living Progress Note** is an evolving, persistent document dedicated to a single overarching **Goal or Initiative**.

### Core Operational Rules:

#### 1. Evolve In-Place (No Date Split)
* When you make progress or change architecture, you **edit the existing progress note** rather than creating `progress-part-2.md` or a new daily log.
* Keep the note scannable, reflecting **current truth**.

#### 2. Rely on Git for the Chronological Timeline
* You do not need to clutter the file with 50 timestamped headers (*"Update Aug 14...", "Update Aug 21..."*).
* **Git history is the permanent timeline.** Run `git log -p progress-note.md` to see exactly how your thinking, code, and milestones evolved over weeks and months. (See [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]]).

#### 3. Hub for Deep Research & Executable Tools
* The progress note connects high-level intent to concrete technical assets:
  * Links upward to overarching vision notes (e.g. `[[public/grow memory|grow memory]]`).
  * Links outward to deep research notes (e.g. `[[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]]`).
  * Links downward to executable skills and code tools (e.g. `[[public/pkm-search|pkm-search]]`).

---

## 📝 Standard Progress Note Template

```markdown
---
tags:
  - progress
  - initiative
status: active # active | blocked | paused | completed
goal: "One-sentence statement of what success looks like."
---

# Progress: [Initiative Name]

> **Goal:** High-level description of what we are building and why it matters.

---

## 🟢 Current State (What Works Now)
* Summary of verified components, active implementations, and solid conventions.

## 🟡 Active Experiments & Next Steps
- [ ] Immediate next experiment or feature to test.
- [ ] Key design decision awaiting resolution.

## 🔴 Blockers & Open Questions
* Hard obstacles, performance issues, or architectural tensions currently under investigation.

## 📚 Connected Research & Tools
* Deep Research: [[relevant research note]]
* Working Tools: [[executable skill or CLI tool]]
* Conceptual Worldview: [[parent concept note]]
```

---

## 🌟 Live Vault Examples

Here are live examples of living progress notes implementing this paradigm:

1. **[[public/progress - agentic biomimetic vault|progress - agentic biomimetic vault]]**
   * *Goal:* Transform the vault into an organic second brain that mimics biological memory consolidation, forgetting curves, and cognitive sparring.
   * *Connects:* [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]], [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]], [[public/grow memory|grow memory]].
2. **[[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]]**
   * *Goal:* Build a sub-5ms hybrid (dense vector + FTS5) retrieval engine with 0% idle CPU overhead that operates 100% locally.
   * *Connects:* [[public/pkm-search|pkm-search]], [[public/pkm metadata indexer|pkm metadata indexer]], [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]].
3. **[[public/progress - fearless vault consolidation and pruning|progress - fearless vault consolidation and pruning]]**
   * *Goal:* Eliminate vault hoarding and context bloat by aggressively pruning and consolidating active notes while leveraging Git history as the forensic deep tape.
   * *Connects:* [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]], [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], [[public/vault synapse pruning|vault synapse pruning]].

---

## 🔗 Related Notes
- [[public/grow memory|grow memory]] — 3-tier hierarchical memory consolidation
- [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]] — working vault as neocortex + Git as deep memory
- [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]] — living user profile and episodic memory logs
