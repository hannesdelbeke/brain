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

**[pkm-search on GitHub](https://github.com/hannesdelbeke/brain/tree/main/skills/pkm-metadata-indexer)**, published as the `pkm-metadata-indexer` skill in this vault, is a lightweight, local-first search daemon and CLI utility designed to provide sub-5ms hybrid (lexical + semantic vector) retrieval across large personal knowledge management (PKM) vaults, code repositories, and agent session logs.

---

## 🚀 Core Architecture

`pkm-search` operates as a dual-layer search pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                      PKM-SEARCH PIPELINE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. DAEMON LAYER ([[searchd.py]])                            │
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

When running [[searchd.py]] as an always-on background daemon on multi-core laptops or workstations:

### 1. ONNX Intra-Op Thread Pool Configuration
By default, ONNX Runtime's thread pool busy-spins between keepalive encodes (every 250ms), burning CPU on multi-core machines with no active queries. Fixed: `get_embedding_model()` takes a `threads` argument, part of the model cache key, and the query path passes `QUERY_THREADS = 1`. Bulk embedding leaves it unset and keeps the full pool, where the parallelism is real work.

Measured on a 12-core laptop, encoding one string every 250ms the way the keepalive loop does:

| threads | idle cores | per encode |
| --- | --- | --- |
| unset | 11.93 | 3.8ms |
| 2 | 0.96 | 5.1ms |
| 1 | 0.05 | 8.6ms |

The extra 4.8ms per encode is invisible inside a 13-22ms query. End to end the daemon now measures 0.000 cores over 20s idle with warm queries at 17ms.

The session-level switch below looks like the direct fix, but `fastembed.TextEmbedding` accepts no `SessionOptions`, so that route means building the ONNX Runtime session yourself instead of going through fastembed. Its `threads=` argument reaches the same pool, which is why the one-line version wins:

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
- [[public/2026-08-27 tail reads, resuming an index at the byte it stopped at|tail reads]] — Reindexing an append-only corpus by parsing only what was appended
- [[public/2026-08-27 what already exists, prior art for a local hybrid search engine|what already exists]] — The plugins, engines and log shippers that got here first, and the two things left
