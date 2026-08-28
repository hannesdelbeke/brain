---
date: 2026-08-28
created: 2026-08-28
tags:
  - technical
  - pkm
  - architecture
  - indexing
aliases:
  - header extraction
  - heading extraction
  - outline extraction
  - structural skeleton extraction
---

# Header Extraction

**Header extraction** is the process of parsing a [[Markdown]] document's structural hierarchy (headings `#`, `##`, `###`), line boundaries, and [[YAML front matter]] metadata to produce a compact outline or document skeleton.

Instead of processing an entire text file, header extraction isolates the document's navigational topology.

Related: [[header extraction for token-efficient retrieval]], [[chunking]], [[YAML front matter]], [[tree-sitter]], [[Markdown]], [[Obsidian]], [[skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[2026-08-27 a link graph over code, docs and assets|link graph]]

---

## 1. Core Mechanics

Header extraction reads a document as a tree or list of sections:
* **Headings:** Identifies heading levels (`H1` through `H6`) and section titles.
* **Line Anchors:** Records the `start_line` and `end_line` offsets for each section block.
* **Metadata & Thesis:** Captures [[YAML front matter]] tags, aliases, and initial lead paragraphs.

This can be implemented via regex line scanning (`^#{1,6}\s+`), [[tree-sitter]] AST parsing, or Markdown parsers.

---

## 2. Common Applications

* **Section-Level Indexing:** Used by [[pkm metadata indexer]] to store atomic section rows in SQLite and generate [[vector embedding|vector embeddings]] per heading rather than averaging entire files.
* **TOC & Navigation:** Powers table-of-contents sidebars, folding, and outline panes in [[Obsidian]].
* **Token-Efficient Retrieval:** Enables [[AI agent|AI agents]] to evaluate document relevance and execute targeted line-range reads without loading full files into context. See [[header extraction for token-efficient retrieval]].
