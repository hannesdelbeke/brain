---
created: 2026-08-31
tags:
  - pkm
  - search
  - architecture
  - performance
  - sqlite
aliases:
  - lightweight vs full index pass
  - pkm indexing tradeoffs
  - pkm metadata vs vector embedding
---

The local PKM indexer operates in two distinct modes: a **lightweight pass (`--skip-embeddings`)** that extracts metadata, link graph edges, and SQLite FTS5 full-text indices in ~1.3 seconds, and a **full pass** that computes dense neural vector embeddings (`BAAI/bge-small-en-v1.5`) across all note sections. For 95%+ of day-to-day workflows and AI agent queries, the lightweight pass provides full retrieval capability without multi-core CPU fan noise or battery drain.

Related: [[vault hybrid search]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[progress - local-first search daemon and indexer]], [[offline GPU embeddings with incremental cache]]

## Comparison matrix

| Dimension | Lightweight Pass (`--skip-embeddings`) | Full Pass (with Vector Embeddings) |
| :--- | :--- | :--- |
| **Duration** | **~1.3 seconds** over 2,900+ notes | **~15–20 minutes** cold CPU build |
| **CPU & fan load** | Instant burst; 0 sustained fan noise | 100% multi-core sustained CPU burn |
| **Frontmatter** | Fully parsed (`tags`, `aliases`, `created`, `energy`) | Fully parsed |
| **Wikilink graph (`edges`)** | Fully built (backlinks, orphans, unlinked mentions) | Fully built |
| **Lexical search (FTS5)** | Full BM25 token matching across all headings/prose | Full BM25 token matching |
| **Semantic vectors** | Skipped | Generates 384-dim dense vectors (`bge-small-en-v1.5`) |
| **Search retrieval** | Exact words, phrases, wildcards, titles, tags, links | Abstract thematic similarity without shared keywords |

## 1. What the lightweight pass does

The lightweight pass scans markdown directly using Python's standard library and SQLite:

* **Frontmatter metadata:** Extracts YAML frontmatter into structured columns (`notes` table) for SQL filtering by tag, creation date, or status.
* **Heading-level sectioning:** Chunks files by `## Heading` into the `sections` table, preserving exact line numbers and chunk SHA256 hashes.
* **Wikilink graph edges:** Parses `[[wikilinks]]` into the `edges` table, powering instant backlink lookups, orphan detection, and unlinked mention queries.
* **SQLite FTS5 full-text index:** Updates the `sections_fts` virtual table using BM25 token ranking. Queries for exact names, tool configurations, acronyms, or syntax run in under 20ms.
* **Throughput:** Processes ~3,700 notes/sec and ~13,600 links/sec.

## 2. What the full vector pass adds

The full pass runs every section through a local transformer model (`BAAI/bge-small-en-v1.5` via `fastembed` / ONNX Runtime):

* **Dense vector embeddings:** Encodes each text chunk into a 384-dimensional float32 vector blob stored in the `sections` table.
* **Thematic / synonym retrieval:** Enables finding conceptually related notes when exact terminology differs (e.g. mapping "depletion from multitasking" to "attention residue across client contexts").
* **SHA256 vector reuse:** Embeddings are keyed by chunk SHA256 hash. Once a cold pass completes, subsequent runs only compute vectors for newly written or edited sections, taking seconds.
* **Downstream consumers:** Powers reciprocal rank fusion (`RRF`), nearest-neighbor note clustering (`GET /similar`), duplicate note detection (`GET /duplicates`), and the Obsidian Semantic Local Graph.

## 3. When each mode is needed

### Lightweight pass is sufficient for:
* **Day-to-day editing and agent retrieval:** Searching for known topics, tools, daily logs, meeting notes, scripts, or architectural proposals.
* **Graph traversal and backlinks:** Querying inbound/outbound links, finding unreferenced assets, or auditing orphan notes.
* **Battery-conscious and quiet work:** Running instant index refreshes without triggering laptop cooling fans.

### Full pass is needed for:
* **Vague / exploratory search:** Asking open conceptual questions without knowing what keywords exist in the vault.
* **Visual semantic graphs & clustering:** Visualizing high-dimensional semantic proximity in Obsidian or auditing vault duplicate clusters.
* **Populating the initial cache:** Running once (or throttled with fewer threads/`nice -n 19`) so future incremental vector updates take <2 seconds.

## 4. Options to run the full pass less aggressively

Building 8,000+ vector embeddings cold on a multi-core CPU defaults to maxing all available cores, which spins up laptop cooling fans. You can throttle the build using OS-level process controls:

* **Core affinity pinning (`taskset -c 0,1`):** Restricts the embedding process to 2 specific CPU cores (out of 12). The remaining 10 cores stay completely idle, keeping total system CPU under ~15–20% and preventing thermal fan spin:
  ```bash
  taskset -c 0,1 python skills/pkm-metadata-indexer/index_pkm_meta.py
  ```
* **Lowest CPU scheduling priority (`nice -n 19`):** Instructs the OS scheduler to only allocate CPU cycles when no foreground interactive process needs them:
  ```bash
  nice -n 19 python skills/pkm-metadata-indexer/index_pkm_meta.py
  ```
* **Combined quiet background execution:** Runs the full pass at the lowest CPU/IO priority pinned to two cores:
  ```bash
  ionice -c 3 nice -n 19 taskset -c 0,1 python skills/pkm-metadata-indexer/index_pkm_meta.py
  ```
* **Per-batch SQLite checkpoints:** The indexer automatically commits vector embeddings in 32-section chunks. If cancelled or interrupted, progress is never lost—re-running immediately skips already-embedded sections via SHA256 cache.
