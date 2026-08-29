---
tags:
- pkm
- ai
- prompting
- graph-theory
- workflow
aliases:
- when to use wikilinks in AI notes
- wikilink heuristics for AI notes
- prompt guidelines for wikilinking
---

# When to Request Wikilinks from AI in Notes

Actionable decision framework and prompt heuristics for when AI agents should generate `[[wikilinks]]` versus keeping plain text in a vector-indexed personal knowledge management (PKM) vault.

Related: [[public/why vector search obsoletes empty stub wikilinks|why vector search obsoletes empty stub wikilinks]], [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks and semantic links]], [[AGENTS.md]]

---

## 🟢 1. When to Use Wikilinks (High Value)

Use explicit `[[wikilinks]]` when an edge adds structural, deterministic, or navigational value that vector search cannot deliver on its own:

1. **Foundational Hardware & Entity Anchors:**
   * Grounding claims in concrete machines, hardware, or core software notes that already exist in the vault.
   * *Example:* `[[public/Lenovo ThinkPad X1 Yoga Gen 7|Lenovo ThinkPad X1 Yoga Gen 7]]`, `[[public/Krita|Krita]]`, `[[Barrier]]`.
2. **Causality, Troubleshooting & Setup Logs:**
   * Documenting sequential troubleshooting steps, root causes, or prerequisite chains in setup logs so humans and GraphRAG agents can traverse the reasoning chain.
   * *Example:* Linking `[[public/2026-08-29 Krita pen lag and stylus latency on Linux|Krita pen lag on Linux]]` from a general Linux setup log.
3. **In-Context Functional Relationships:**
   * Explaining the relationship directly within the flow of a sentence rather than dumping a blind list at the bottom.
   * *Example:* `"We tuned the Wacom AES polling rate to match the [[public/Lenovo ThinkPad X1 Yoga Gen 7|ThinkPad's digitizer]]."`
4. **Skills, Tooling & Automation Scripts:**
   * Referencing executable scripts, workflows, or agent capabilities.
   * *Example:* `[[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]`.

---

## 🔴 2. When to Keep Plain Text (Zero Value / Harmful)

Keep terms as unlinked plain text when explicit brackets create graph noise or redundant overhead:

1. **Speculative / Unwritten Concepts (Empty Stubs):**
   * If a model, library, or tool is mentioned in passing and has no dedicated note, write plain text (e.g. `Gemini Flash 3.7`, `uv`, `polars`).
   * *Why:* Vector embeddings and SQLite FTS5 index plain text automatically. Empty stubs pollute the graph view and waste agent context during multi-hop retrieval. See [[public/why vector search obsoletes empty stub wikilinks]].
2. **Generic Dictionary Words:**
   * Never link broad, non-specific words (e.g. `[[laptop]]`, `[[system]]`, `[[database]]`, `[[AI]]`).
   * *Why:* Causes graph hyper-connectivity ("graph seizures") and destroys retrieval precision.
3. **Standard Syntax, APIs & Package Names:**
   * Generic programming libraries or command-line tools mentioned in shell snippets (`import json`, `git status`).

---

## 📋 The 3 Hard Guardrails for AI Agent Prompts

When instructing an AI agent to write or refactor notes, enforce these rules from [[AGENTS.md]]:

1. **Verify Before Linking (No Dead Links):** Never generate speculative links. The target note must already exist on disk or be explicitly created during the same turn.
2. **Link in Context:** Embed links naturally into sentences explaining *why* the concepts connect, avoiding detached bottom-of-page link dumps.
3. **Respect Vault Privacy Boundaries:** Notes in `public/` must never link across submodule boundaries into private root or company-specific directories.

---

## 💡 Recommended Prompt Template

When instructing an AI to create notes:

> *"Draft this note. Use `[[wikilinks]]` only for existing canonical concept notes and hardware entities in the vault. Do not create speculative or empty stub links—leave unwritten terms as plain text for vector search."*

---

## References
- [[public/why vector search obsoletes empty stub wikilinks|why vector search obsoletes empty stub wikilinks]] — Why vector search and FTS replace manual backlink hacks
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks and semantic links]] — Biological synaptic graph models vs binary wikilinks
- [[AGENTS.md]] — Core vault instructions for agent authoring, link validation, and privacy invariants
