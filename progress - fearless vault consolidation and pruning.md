---
date: 2026-08-27
created: 2026-08-27
tags:
  - progress
  - initiative
  - pkm
  - git
  - refactoring
status: active
goal: "Eliminate vault hoarding and context bloat by aggressively distilling active notes into high-signal gists while leveraging Git history as the permanent forensic memory layer."
aliases:
  - progress - fearless vault consolidation and pruning
  - vault consolidation progress
  - fearless refactoring progress
---

# Progress: Fearless Vault Consolidation & Pruning

> **Goal:** Transition the vault from an append-only digital graveyard into a high-signal neocortical surface. Enable ruthless refactoring, merging, and pruning of active notes while relying on Git history as the permanent, forensic hippocampal deep tape that AI agents can query on demand.

---

## 🟢 Current State (What Works Now)

* **The Two-Tier Architecture Established:** Formalized the separation between the **Living Foreground** (working vault of clean, distilled gists) and the **Immutable Deep Tape** (Git history object store) ([[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]]).
* **AI Git Archaeology Protocol:** Standardized agent commands for resurrecting pruned historical code, hex logs, and deleted exploratory notes via `git log -S "<symbol>" -p` and `git show <sha>:<path>`.
* **Private-to-Public Promotion SOP:** Established strict upward-only link hierarchy rules and the Diff-First approval loop to ensure zero private data leakage when promoting notes ([[public/skills/private-to-public-note-promotion/SKILL|private to public note promotion]]).
* **Semantic Synapse Pruning Model:** Modeled note decay on biological sleep homeostasis (Tononi's SHY), providing a scientific foundation for pruning weak links and archiving low-heat notes ([[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], [[public/vault synapse pruning|vault synapse pruning]]).

---

## 🟡 Active Experiments & Next Steps

- [ ] **Automated Multi-Stub Overnote Merger:** Run an agent pass to identify clusters of 3–5 fragmented exploratory notes on related subjects (e.g. legacy BLE logs) and merge them into single definitive skills/notes, deleting the exploratory stubs.
- [ ] **Nightly Synaptic Weight Decay Script:** Build a background daemon pass that applies exponential decay to the dynamic `synaptic_edges` table in `pkm_index.db`, flagging orphan edges below threshold.
- [ ] **Semantic Diff Search Integration:** Wire GPU-accelerated deleted chunk indexing to search across past Git diffs semantically ([[public/semantic search on git history|semantic search on git history]]).

---

## 🔴 Blockers & Open Questions

* **No Pruning Has Happened Yet:** The vault is at 3,253 notes and still growing. The architecture is written; no note has been merged or deleted under it. See [[public/2026-08-27 agentic pkm action plan|agentic pkm action plan]] — do one manual multi-stub merge before automating the merger.
* **Obsidian In-Memory Tab Clashes:** Obsidian autosave re-creates deleted root files if an open tab isn't closed before disk deletion (`Ctrl + W` protocol required).

---

## 📚 Connected Research & Tools

* **Core Architecture:** [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]]
* **Consolidation Ladder:** [[public/grow memory|grow memory]]
* **Synaptic Graph Theory:** [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]]
* **Vault Pruning Strategies:** [[public/vault synapse pruning|vault synapse pruning]], [[public/vault graph complexity|vault graph complexity]]
* **Git History Search:** [[public/semantic search on git history|semantic search on git history]], [[public/rewrite git history for ai authorship migration|rewrite git history for ai authorship migration]]
