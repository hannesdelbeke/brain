---
date: 2026-08-27
created: 2026-08-27
tags:
  - pkm
  - memory
  - architecture
  - ai
  - consolidation
  - philosophy
aliases:
  - grow memory
  - growing memory
  - hierarchical memory consolidation
  - evolving concept notes from logs
---

# Grow Memory: Hierarchical Knowledge Consolidation from Raw Logs to Semantic Concepts

How to evolve a personal knowledge vault by continuously consolidating information across three cognitive tiers—moving beyond arbitrary calendar-based reviews (weekly/monthly) into **concept-driven memory growth**, where raw trial-and-error logs are distilled into permanent mental models while human motivations remain firmly anchored.

Related: [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]], [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]], [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]], [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]]

---

## 🚫 The Trap of Calendar-Bound Reviews

Traditional PKM advice forces knowledge into artificial calendar buckets: *"Do a daily review, then a weekly review, then a monthly review."*

In practice, calendar-bound reviews fail because:
1. **Thoughts Don't Conform to 30-Day Cycles:** A reverse-engineering breakthrough on BLE protocols or a deep insight into token economics doesn't belong to "August 2026"; it belongs to your permanent semantic understanding of hardware automation and LLM architecture.
2. **Review Fatigue:** Humans burn out summarizing chronological logs rather than evolving living concepts.
3. **No Structural Elevation:** Summarizing 30 daily logs into a "monthly note" just creates a larger, slightly less chaotic log file. It does not evolve your permanent mental models.

Instead of time-based consolidation, knowledge should **grow hierarchically across 3 cognitive levels**.

---

## 🏔️ The 3-Tier Memory Hierarchy

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE MEMORY GROWTH LADDER                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   TIER 3: HIGH-LEVEL (Semantic Concepts & Human Intent)                │
│   • Evolving concept overnotes (`[[ble-reverse-engineering]]`)         │
│   • Core human motivations (*"Why we did this: local HAOS control"*)   │
│   • Cross-domain principles, mental models & architectural rules.      │
│   • Confidence: High strategic alignment | Permanent in vault          │
│                                  ▲                                     │
│                                  │ (Consolidation & Abstraction)       │
│                                                                        │
│   TIER 2: MID-LEVEL (Task Synthesis & Problem Solutions)               │
│   • Distilled summary notes generated via fast LLM (Gemini Flash).     │
│   • Working code recipes, verified commands, reproducible steps.       │
│   • Confidence: 0.8–0.9 (Empirically verified in practice)             │
│   • Raw trial-and-error notes deleted after synthesis.                 │
│                                  ▲                                     │
│                                  │ (Extraction & Distillation)         │
│                                                                        │
│   TIER 1: LOW-LEVEL (Ground Truth & Perception)                        │
│   • Raw machine logs, Wireshark traces, terminal errors, sensor dumps. │
│   • Confidence: 1.0 (Hard factual data)                                │
│   • Ephemeral: Captured in daily scratchpads, preserved in Git.        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 1. Low-Level: Ground Truth & Perception
* **What It Holds:** Exact terminal output, raw BLE hex packets, sensor telemetry, system error codes, and verbatim quotes.
* **Confidence Rating:** **1.0 (Factual Truth)**. It either happened or it didn't.
* **Lifecycle:** Ephemeral in the working vault. Written into daily scratch notes during active exploration. We do not keep 500 lines of raw hex dumps in permanent markdown files—we let Git retain the deep forensic trace while the working note is kept lean.

### 2. Mid-Level: Task Synthesis & Episodic Compression
* **What It Holds:** Distilled solutions created after an experiment succeeds.
* **The Process:** A fast model (e.g. Gemini Flash) reads the chaotic low-level scratchpad and synthesizes a structured, readable summary note containing only the working solution, the root cause, and the key commands.
* **Fearless Deletion:** Once the synthesis is verified, the original exploratory stub notes are deleted. **We don't care about the exact dead-end logs; we care about the learnings.** (See [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]]).
* **Confidence Rating:** **0.8–0.9 (Working Solution)**.

### 3. High-Level: Semantic Concepts & Human Motivation
* **What It Holds:** Permanent, evolving concept notes (e.g. `[[digital encryption]]`, `[[local-first home automation]]`, `[[neural search daemons]]`).
* **The Human Intent Anchor:** Crucially, Tier 3 captures **why** the human initiated the project:
  * *Example:* *"Frustration with proprietary vendor cloud apps that require third-party logins. The goal is 100% local Home Assistant control over Bluetooth blinds without cloud egress."*
* **Semantic Growth:** When a new mid-level note is produced, the system does not just file it away; it updates and enriches the parent concept notes, weaving new evidence into your overarching worldview.

---

## 🛠️ Concrete Case Study: The Bluetooth Blind Automation

Here is how a real engineering task moves through the memory growth ladder:

```
[ PHASE 1: RAW DUMP (Tier 1) ]
• Daily Log / Scratchpad captures raw nRF Connect logs, Bluetooth MAC addresses,
  and failed gatttool commands.
• Confidence: 1.0 (Machine Ground Truth).

[ PHASE 2: SYNTHESIS & PRUNING (Tier 2) ]
• Gemini Flash processes the raw session log.
• Produces a clean 40-line Python controller script and checksum algorithm.
• Deletes 3 temporary debugging scratchpads.
• Working note created: `skills/ble-device-reverse-engineering/SKILL.md`.

[ PHASE 3: CONCEPT EVOLUTION & INTENT ANCHORING (Tier 3) ]
• The high-level concept note `[[ble-device-reverse-engineering]]` is updated.
• Cross-linked with `[[local-first home automation]]` and `[[smart home sovereignty]]`.
• Motivation recorded: "Eliminated vendor cloud dependency for motorized blinds."
```

---

## 🧠 Why This Works: Stealing from Biological Memory

This 3-tier architecture directly mirrors the biological consolidation mechanisms described in [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]]:

1. **Hippocampus to Neocortex:** Tier 1 acts like the hippocampus (temporary high-fidelity recording of daily events). Sleep consolidation (Tier 2 synthesis) extracts the generalized patterns into neocortical concept schemas (Tier 3), discarding the raw noise.
2. **Confidence Calibration:** Low-level machine logs are grounded at 1.0 confidence. Inferred patterns and synthesized gists carry explicit confidence scores, preventing the AI buddy from confusing an exploratory hypothesis with an established fact.
3. **Hebbian Synaptic Growth:** Frequently co-activated concepts strengthen their link weights over time, forming natural clusters of expertise without manual taxonomy maintenance.

---

## 🔗 Related Notes
- [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]] — 3-timescale automated consolidation and living user profiles
- [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]] — slow-wave sleep consolidation and lossy abstraction
- [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]] — working vault as neocortex + Git history as deep memory
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] — Hebbian weighting and synaptic pruning
- [[public/skills/ble-device-reverse-engineering/SKILL|ble device reverse engineering]] — concrete implementation of local Bluetooth reverse engineering
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]] — local SQLite metadata compiler and search daemon
