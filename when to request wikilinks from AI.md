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

Decision framework and prompt heuristics for when AI agents should generate `[[wikilinks]]` versus keeping plain text in a vector-indexed PKM vault.

Related: [[vector search obsoletes empty stub wikilinks]], [[2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], [[AGENTS.md]]

## When to wikilink

Use explicit `[[wikilinks]]` only when an edge adds structural, deterministic, or navigational value that vector search can't deliver on its own:

- **Hardware & entity anchors:** Ground claims in concrete hardware or software notes that already exist on disk (e.g. `[[Lenovo ThinkPad X1 Yoga Gen 7]]`, `[[Krita]]`, `[[Barrier]]`).
- **Causality & setup logs:** Document sequential troubleshooting steps, root causes, or prerequisite chains (e.g. linking `[[2026-08-29 Krita pen lag and stylus latency on Linux|Krita pen lag on Linux]]` from a setup log).
- **In-context relationships:** Explain the connection directly inside sentences instead of dumping blind link lists at the bottom (e.g. `"tuned Wacom AES polling rate to match the [[Lenovo ThinkPad X1 Yoga Gen 7|ThinkPad digitizer]]"`).
- **Skills & tooling:** Reference executable agent skills or workflows (e.g. `[[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]`).

## When to keep plain text

Keep terms unlinked when brackets create graph noise or empty stub overhead:

- **Speculative or unwritten concepts:** If a tool or library is mentioned in passing without a dedicated note, write plain text (e.g. `Gemini Flash 3.7`, `uv`, `polars`). Vector embeddings and SQLite FTS5 index plain text automatically. Empty stubs pollute the graph view and waste agent tokens during multi-hop retrieval. See [[vector search obsoletes empty stub wikilinks]].
- **Generic dictionary words:** Never link broad terms like `laptop`, `system`, or `database`. It causes hyper-connected nodes and degrades retrieval precision.
- **Standard syntax & package names:** Code identifiers, standard libraries, or shell snippets (`import json`, `git status`).

## Prompt guardrails

When instructing an AI agent to write or edit notes, enforce these rules from [[AGENTS.md]]:

- **No dead links:** Never create speculative links. The target note must already exist on disk.
- **Link in context:** Integrate links naturally into sentences explaining the connection.
- **Respect privacy boundaries:** Public notes must never link across submodules into private or company-specific directories.
- **Short links:** Prefer short link targets over deep paths (e.g. `[[note]]` over `[[public/note]]`).

## Prompt template

When prompting an AI to draft or refactor notes:

> *"Draft this note. Use `[[wikilinks]]` only for existing canonical concept notes and hardware entities in the vault. Don't create speculative or empty stub links—leave unwritten terms as plain text for vector search."*
