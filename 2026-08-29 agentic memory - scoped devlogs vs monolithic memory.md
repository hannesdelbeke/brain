---
date: 2026-08-29
created: 2026-08-29
tags:
  - ai
  - agents
  - memory
  - architecture
  - pkm
  - devlog
aliases:
  - example agentic learning
  - scoped agent memory
  - 2026-08-29 agentic memory - scoped devlogs vs monolithic memory
---

# 🧠 Agentic Memory: Scoped Devlogs, Tool Isolation, and Atomic Learnings

How to structure AI memory and retrospective learning without succumbing to bloated global error files, combining project-specific repositories, scoped devlogs, and [[atomic notes]].

Related: [[2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat]], [[2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]], [[2026-08-27 Mem0 memory architecture - cloud pricing, security, and local privacy|Mem0 memory architecture]], [[2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]], [[atomic notes]], [[token efficient PKM analysis architecture]], [[2026-08-29 Startup Metrics Logger devlog]]

---

## 🚫 The Anti-Pattern: The Global Monolithic Memory Dump

When building or collaborating with AI agents, the initial human instinct is often to maintain a single global `MEMORIES.md`, `LEARNINGS.md`, or `ERRORS.md` file.

```
┌─────────────────────────────────────────────────────────────┐
│                 GLOBAL MEMORY ANTI-PATTERN                  │
│                                                             │
│  Plugin A linter failure  ──┐                               │
│  React hook syntax bug    ──┼──► GLOBAL_LEARNINGS.md        │
│  Git OAuth scope quirk    ──┤    (Dumping ground, 1k+ lines)│
│  Blender API deprecation  ──┘                               │
│                                            │                │
│                                            ▼                │
│                              Context Pollution              │
│                              Cross-Domain Noise             │
│                              Unbounded Token Waste          │
└─────────────────────────────────────────────────────────────┘
```

This global dump degrades agent performance for three reasons:
1. **Cross-Domain Noise:** A lesson about Obsidian manifest validation (`manifest.json: no "Plugin" in name`) pollutes context when the agent is writing a Python CLI tool or Blender addon.
2. **Context Budget Exhaustion:** Injecting an ever-growing global error log wastes thousands of input tokens on every turn.
3. **Contradictions & Outdated State:** Rules recorded for one framework clash with another (e.g. strict typing rules across different environments).

---

## 💡 The Scoped & Atomic Architecture

Instead of a monolithic memory file, agentic knowledge is distributed into **tightly scoped, domain-isolated layers** following the [[atomic notes]] principle:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        SCOPED AGENTIC MEMORY                             │
│                                                                          │
│  ┌───────────────────────┐         ┌──────────────────────────────────┐  │
│  │   TOOL REPOSITORY     │         │       VAULT SCOPED DEVLOG        │  │
│  │  • Source code        │         │  • Retrospective bullet points   │  │
│  │  • README & docs      │ ◄─────► │  • Specific mistakes & fixes     │  │
│  │  • Distribution build │         │  • Local vault wikilinks         │  │
│  └───────────────────────┘         └──────────────────────────────────┘  │
│             │                                        │                   │
│             ▼                                        ▼                   │
│    Zero AI Memory Bloat                   Just-In-Time Context Ingestion │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1. Tool-Level Artifacts Stay in the Tool Repo
* Pure implementation code, packaging configurations, test suites, and user-facing documentation belong strictly in the standalone repository (e.g., [obsidian-startup-metrics-logger](https://github.com/hannesdelbeke/obsidian-startup-metrics-logger)).
* Keeps the tool maintainable, forkable, and clean for external contributors.

### 2. Retrospective Learning Stays in Scoped Devlogs
* When mistakes, linter rejections, or unexpected platform quirks occur, record them in a **dedicated, single-topic devlog** in the knowledge base (e.g. [[2026-08-29 Startup Metrics Logger devlog]]).
* Format learnings as concise 1-line bullet points detailing:
  - The exact failure mode.
  - The root cause.
  - The exact resolution applied.

### 3. Atomic Concept Integration
* High-level architectural patterns discovered during development are distilled into distinct [[atomic notes]] (e.g. [[2026-08-29 Obsidian lazy loading plugins compared]], [[2026-08-29 Obsidian community plugin submission process]]).
* The agent only pulls in the specific note relevant to the active task, achieving maximum reasoning clarity with minimal token overhead.

---

## 🎯 Case Study: Startup Metrics Logger Workflow

A live example of this memory separation in practice:

1. **Tool Source & Packaging:**
   * Repository: [hannesdelbeke/obsidian-startup-metrics-logger](https://github.com/hannesdelbeke/obsidian-startup-metrics-logger)
   * Contains only code, tests, manifest, and user documentation.
2. **AI Retrospective & Mistakes Log:**
   * Devlog Note: [[2026-08-29 Startup Metrics Logger devlog]]
   * Documents model-specific errors (load order array positioning, manifest naming rules, Platform API vs navigator) so future sessions on this plugin immediately inherit past lessons.
3. **Modular Domain Knowledge:**
   * Ecosystem Guides: [[2026-08-29 Obsidian lazy loading plugins compared]] and [[2026-08-29 Obsidian community plugin submission process]].
   * Reusable by agents across other Obsidian-related tasks without dragging in unrelated project telemetry.

---

## 🔗 Related Notes
- [[2026-08-28 agent instruction bloat - modular skills and compact synthesis]]
- [[2026-08-27 what an AI buddy actually needs]]
- [[2026-08-27 Mem0 memory architecture - cloud pricing, security, and local privacy]]
- [[2026-08-27 fearless note consolidation - using git history as the deep memory layer]]
- [[2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution]]
- [[atomic notes]]
- [[token efficient PKM analysis architecture]]
- [[2026-08-29 Startup Metrics Logger devlog]]
