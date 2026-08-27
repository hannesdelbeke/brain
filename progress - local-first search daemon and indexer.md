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
* **Zero Idle CPU:** The ONNX thread pool spinning between 250ms keepalive encodes cost 11.93 cores on a 12-core laptop. Capping the query path at `QUERY_THREADS = 1` (threads=2 burns 0.96 cores, threads=1 burns 0.05) brings the warm daemon to 0.000 cores over 20s idle with warm queries at 17ms, paying 3.8ms → 8.6ms per encode. Bulk embedding keeps the full pool. Proof: run the keepalive pattern for 20s under `psutil.Process().cpu_percent()` and it reads 0.035 cores over 77 encodes; `python -m unittest test_index_pkm_meta test_searchd` pins the fix so a future edit cannot silently drop it ([[public/pkm-search|pkm-search]]).

* **No Vendor Lock-In:** The engine imports no assistant SDK — `grep -rn anthropic --include=*.py` returns nothing. Embeddings are local `bge-small-en-v1.5` through ONNX, so retrieval never calls a hosted model; the daemon is plain HTTP on `127.0.0.1:44771`, so any client that can issue a GET can query it; the source of truth is markdown in git. The only vendor-shaped part is the session-transcript scanner (`~/.claude/projects`), and it sits behind the `--corpus` seam as one scanner among several.

---

## 🟡 Active Experiments & Next Steps

- [ ] **Sync the Two Copies:** `skills/pkm-metadata-indexer/` here and the standalone repo still diverge. The vault copy is ahead on features: `urgent_tasks.py`, `mention_heatmap.py`, `find_similar_notes` and `/similar`, `find_unlinked_mentions` and `/unlinked` with its `--unlinked` CLI flag, plus the tests and SKILL.md sections for all of it. The standalone copy is ahead only on defaults and packaging: keepalive is on by default there (`--no-keepalive`) against opt-in `--keepalive` here, and it carries a `README.md` the vault copy has no use for. `find_open_problems.py` differs by line endings only. The thread-pool fix is now applied on both sides. Direction of the merge is vault → standalone for everything except the keepalive default, which needs a decision.
- [ ] **Section-Level SHA256 Invalidation:** Update `index_pkm_meta.py` schema from note-level SHA256 to section-level SHA256 so editing a single heading doesn't re-embed all 6.8 sections of a note.
- [ ] **Write-Path Near-Neighbor Gate:** Wire title embeddings to the note-creation path to detect near-duplicates before writing new notes.
- [ ] **Prove the Scanner Seam Is Vendor-Neutral:** Write a second transcript scanner for another agent CLI returning the same `(notes, sections, links, errors)` tuple. Until a second one exists, "one scanner among several" is a claim rather than a fact. Any summarisation added later goes through an OpenAI-compatible endpoint (Ollama serves one locally) so the same code runs against a local or hosted model.
- [ ] **Evaluate `sqlite-vec`:** Benchmark native C-extension `sqlite-vec` against in-process NumPy matrix multiplication for cold queries.

---

## 🔴 Blockers & Open Questions

* **DirectML GPU Initialization Latency:** On initial cold startup on Windows, DirectX 12 driver compilation takes 3–5 seconds before the model enters memory.
* **No Query Logging:** `searchd.py` records neither queries nor result sets, so every retrieval-driven idea downstream (co-retrieval weighting, synaptic edges, ranking evaluation) has no data to run on. Designed out in [[public/2026-08-27 every read is a write - co-retrieval as synapse strength|every read is a write]], whose v0 is an `origin` parameter on `/search` and one batched insert per result.

---

## 📚 Connected Research & Tools

* **Cross-Initiative Plan:** [[public/2026-08-27 agentic pkm action plan|agentic pkm action plan]]
* **Core Tool Repository:** [[public/pkm-search|pkm-search]]
* **Metadata Indexer & Skill:** [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]
* **Retrieval Economics:** [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]
* **Vault Performance Benchmarks:** [[public/obsidian search and index slow on 5k notes|obsidian search and index slow on 5k notes]]
* **Offline GPU Vector Caching:** [[public/offline GPU embeddings with incremental cache|offline GPU embeddings with incremental cache]]
