---
date: 2026-08-27
created: 2026-08-27
tags:
  - progress
  - initiative
  - search
  - vector
  - python
  - technical
status: active
goal: "Deliver sub-5ms local-first hybrid vector + lexical retrieval across 10,000+ notes with zero cloud egress and zero CPU idle overhead."
aliases:
  - progress - local-first search daemon and indexer
  - search daemon progress
  - pkm search progress
---

# Progress: Local-First Search Daemon & Indexer

> **Goal:** Build and maintain an ultra-fast, local-first search daemon (`pkm-search`) combining ONNX neural embeddings with SQLite FTS5 / Ripgrep, providing sub-5ms location payloads to AI agents while operating 100% offline with zero idle CPU overhead.

---

## 🟢 Current State (What Works Now)

* **Resident Search Daemon (`pkm-search`):** ONNX embedding model kept resident in memory via `searchd.py`, eliminating the 2–5s PyTorch import cold start ([[public/pkm-search|pkm-search]]).
* **Heading-Level Indexing (`##`):** Section-level chunking proven mathematically superior to arbitrary token window slicing, saving 95%+ context tokens by returning lean location payloads `(path, line, heading)` ([[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]).
* **In-Memory NumPy Search:** Proved that brute-force dot product over float32 blobs in NumPy executes in <1ms across 68,000 sections, eliminating the need for heavy vector databases below 300,000 notes.

---

## 🟡 Active Experiments & Next Steps

- [ ] **Fix the Idle CPU Burn (unapplied):** Root cause is ONNX thread-pool spinning between 250ms keepalive encodes. Nothing is configured in the repo yet, and the `ort.SessionOptions` route written up in [[public/pkm-search|pkm-search]] is not reachable through `fastembed.TextEmbedding`, which takes no session options. Reachable levers: `threads=` on the constructor, `OMP_WAIT_POLICY=passive` in the daemon environment, or building the ORT session directly. Acceptance: warm daemon idle 60s under 1% of one core, measured.
- [ ] **Sync the Two Copies:** `skills/pkm-metadata-indexer/` here and the `pkm-search` repo have diverged across 7 files, with `urgent_tasks.py` and `mention_heatmap.py` only in the vault copy.
- [ ] **Section-Level SHA256 Invalidation:** Update `index_pkm_meta.py` schema from note-level SHA256 to section-level SHA256 so editing a single heading doesn't re-embed all 6.8 sections of a note.
- [ ] **Write-Path Near-Neighbor Gate:** Wire title embeddings to the note-creation path to detect near-duplicates before writing new notes.
- [ ] **Evaluate `sqlite-vec`:** Benchmark native C-extension `sqlite-vec` against in-process NumPy matrix multiplication for cold queries.

---

## 🔴 Blockers & Open Questions

* **DirectML GPU Initialization Latency:** On initial cold startup on Windows, DirectX 12 driver compilation takes 3–5 seconds before the model enters memory.
* **No Query Logging:** `searchd.py` records neither queries nor result sets, so every retrieval-driven idea downstream (co-retrieval weighting, synaptic edges, ranking evaluation) has no data to run on.

---

## 📚 Connected Research & Tools

* **Cross-Initiative Plan:** [[public/2026-08-27 agentic pkm action plan|agentic pkm action plan]]
* **Core Tool Repository:** [[public/pkm-search|pkm-search]]
* **Metadata Indexer & Skill:** [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]
* **Retrieval Economics:** [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]
* **Vault Performance Benchmarks:** [[public/obsidian search and index slow on 5k notes|obsidian search and index slow on 5k notes]]
* **Offline GPU Vector Caching:** [[public/offline GPU embeddings with incremental cache|offline GPU embeddings with incremental cache]]
