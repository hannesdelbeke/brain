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

> [!todo] next
> - **next:** Section-level SHA256 invalidation, so editing one heading does not re-embed the whole note.
> - **blocked:** Nothing.

---

## 🟢 Current State (What Works Now)

* **Resident Search Daemon (`pkm-search`):** ONNX embedding model kept resident in memory via `searchd.py`, eliminating the 2–5s PyTorch import cold start ([[public/pkm-search|pkm-search]]).
* **Heading-Level Indexing (`##`):** Section-level chunking proven mathematically superior to arbitrary token window slicing, saving 95%+ context tokens by returning lean location payloads `(path, line, heading)` ([[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]).
* **In-Memory NumPy Search:** Proved that brute-force dot product over float32 blobs in NumPy executes in <1ms across 68,000 sections, eliminating the need for heavy vector databases below 300,000 notes.
* **Zero Idle CPU:** The ONNX thread pool spinning between 250ms keepalive encodes cost 11.93 cores on a 12-core laptop. Capping the query path at `QUERY_THREADS = 1` (threads=2 burns 0.96 cores, threads=1 burns 0.05) brings the warm daemon to 0.000 cores over 20s idle with warm queries at 17ms, paying 3.8ms → 8.6ms per encode. Bulk embedding keeps the full pool. Proof: run the keepalive pattern for 20s under `psutil.Process().cpu_percent()` and it reads 0.035 cores over 77 encodes; `python -m unittest test_index_pkm_meta test_searchd` pins the fix so a future edit cannot silently drop it ([[public/pkm-search|pkm-search]]).

* **No Vendor Lock-In:** The engine imports no assistant SDK — `grep -rn anthropic --include=*.py` returns nothing. Embeddings are local `bge-small-en-v1.5` through ONNX, so retrieval never calls a hosted model; the daemon is plain HTTP on `127.0.0.1:44771`, so any client that can issue a GET can query it; the source of truth is markdown in git. The only vendor-shaped part is the session-transcript scanner (`~/.claude/projects`), and it sits behind the `--corpus` seam as one scanner among several.

---

## 🟡 Active Experiments & Next Steps

- [x] **Session Embeddings:** The transcript corpus carries vectors: 79,359 sections over 858 transcripts, generated in 298.86s at 265.5 vec/s on DirectML, 320.92s for the whole pass, database 222 MB. Warm hybrid queries answer in 34-62ms, against 30-58ms lexical, so the ranking is free at query time; the cost is the 122 MB vector matrix the daemon holds resident. A paraphrase now works — "how did we stop the laptop overheating" returns the session that diagnosed it first, with no shared keyword.
- [x] **Query Logging:** Every `/search` and `/similar` appends a row to `~/.pkm/queries.jsonl` with the query text, the vault, the latency, the result paths and an optional caller-supplied `origin`. A file rather than a table, because a reindex rebuilds the index. This is the producer the co-retrieval and ranking-evaluation work had none of.
- [x] **One Copy of the Engine:** `skills/pkm-metadata-indexer/` is the only copy, and the standalone repo is a `README.md` pointing at it. Keepalive is on by default, `--no-keepalive` turns it off.
- [ ] **Section-Level SHA256 Invalidation:** Update `index_pkm_meta.py` schema from note-level SHA256 to section-level SHA256 so editing a single heading doesn't re-embed all 6.8 sections of a note.
- [ ] **Write-Path Near-Neighbor Gate:** Wire title embeddings to the note-creation path to detect near-duplicates before writing new notes.
- [ ] **Prove the Scanner Seam Is Vendor-Neutral:** Write a second transcript scanner for another agent CLI returning the same `(notes, sections, links, errors)` tuple. Until a second one exists, "one scanner among several" is a claim rather than a fact. Any summarisation added later posts plain JSON to a generate endpoint named by an environment variable, with no SDK and no key in the source, so the same code runs against a local model or a hosted one; and what the model wrote is committed as data, so the index rebuilds with no model running at all. Done once already on a non-vault corpus, where a model rewrote 572 thin one-line summaries; a blind-judge A/B against the old text put precision@10 at 21% against 22%, so the sentences read better and rank the same.
- [ ] **Rework Obsidian Core Features on the Index:** Semantic quick switcher, a local graph that draws meaning as well as links, a duplicate warning on note creation, tag suggestion, orphan-biased random note, and the 1,780 dead wikilinks as a query. Each is listed with its acceptance in [[public/core Obsidian features to rework on the vault index|core Obsidian features to rework on the vault index]].
- [ ] **Derive Edges Outside the Vault:** The link half of the index does not need markdown or Obsidian. One scanner over one repository emitting edges for markdown links, relative path references and image embeds answers "what documents reference this file" and "which images are referenced by nothing", neither of which is answerable today. Designed in [[public/2026-08-27 a link graph over code, docs and assets|a link graph over code, docs and assets]].
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
* **What the Index Should Replace in Obsidian:** [[public/core Obsidian features to rework on the vault index|core Obsidian features to rework on the vault index]]
* **The Link Half, Outside the Vault:** [[public/2026-08-27 a link graph over code, docs and assets|a link graph over code, docs and assets]]
