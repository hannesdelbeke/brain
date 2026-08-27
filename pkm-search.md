---
date: 2026-08-27
created: 2026-08-27
tags:
  - technical
  - pkm
  - search
  - vector
  - python
  - tool
aliases:
  - pkm-search
  - pkm search
  - searchd
  - search daemon
---

# pkm-search

**[pkm-search on GitHub](https://github.com/hannesdelbeke/pkm-search)** is a lightweight, local-first search daemon and CLI utility designed to provide sub-5ms hybrid (lexical + semantic vector) retrieval across large personal knowledge management (PKM) vaults, code repositories, and agent session logs.

---

## 🚀 Core Architecture

`pkm-search` operates as a dual-layer search pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                      PKM-SEARCH PIPELINE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. DAEMON LAYER (`searchd.py`)                            │
│   • Keeps ONNX embedding model resident in memory.          │
│   • Avoids 2–5s PyTorch/transformers cold-start penalty.    │
│   • Responds to local IPC/HTTP socket queries in ~3–5ms.    │
│                                                             │
│   2. HYBRID QUERY ENGINE                                    │
│   • Lexical Search: Ripgrep / SQLite FTS5 for exact tokens  │
│     (filenames, code symbols, error codes, commit hashes).  │
│   • Semantic Search: Dense section-level vector cosine      │
│     similarity (`bge-small-en-v1.5` / `all-MiniLM-L6-v2`).  │
│   • Hybrid Union: Merges and dedupes candidate hits by      │
│     `(path, line_number)`.                                  │
│                                                             │
│   3. LEAN LOCATION PAYLOAD                                  │
│   • Returns `(path, line_number, section_heading, score)`.  │
│   • Never returns full note bodies, saving 95%+ token context│
│     for calling LLMs and AI agents.                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Performance & Stability Best Practices

When running `searchd.py` as an always-on background daemon on multi-core laptops or workstations:

### 1. ONNX Intra-Op Thread Pool Configuration
By default, ONNX Runtime's thread pool can busy-spin between keepalive encodes (every 250ms), causing elevated CPU consumption on multi-core machines even with no active queries.

Reachable configuration levers to ensure true 0% CPU idle:
* **FastEmbed Thread Cap:** Pass `threads=2` directly to `TextEmbedding(..., threads=2)`.
* **Environment Level:** Set `OMP_WAIT_POLICY=PASSIVE` to prevent worker thread spinning.
* **Direct ONNX Session Options:**
  ```python
  import onnxruntime as ort

  session_options = ort.SessionOptions()
  session_options.add_session_config_entry("session.intra_op.allow_spinning", "0")
  session_options.intra_op_num_threads = 2
  ```

### 2. Heading-Level (`##`) Section Indexing
* Rather than chunking notes by arbitrary token windows, `pkm-search` splits on Markdown heading boundaries (`^## `).
* Slicing files by line offset during read operations costs zero extra API round-trips while preserving logical semantic units.

---

## 🔗 Related Notes
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]] — SQLite metadata indexer and schema walk
- [[public/obsidian search and index slow on 5k notes|obsidian search and index slow on 5k notes]] — Benchmarking retrieval bottlenecks in large vaults
- [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]] — Using fast indexers alongside Git history
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] — Hebbian co-retrieval and dynamic edge weighting
