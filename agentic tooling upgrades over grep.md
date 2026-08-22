---
tags:
  - ai
  - tools
  - pkm
  - optimization
---
> [!summary] Plan
> Hybrid search and link indexing are live via [[pkm metadata indexer]]. Keep `rg` for exact keyword and code retrieval; use local FTS5 + BGE-small vector search for semantic themes, synonyms, and duplicate prevention.

Increase agent reply speed and context efficiency across the vault by upgrading from literal `grep` to meaning-based semantic search and link graph traversal.

## Expected Time Savings

- **Thematic & fuzzy search:** Cuts multi-turn synonym guessing (15s over 2–3 agent turns) to a single turn (~3–4s), saving **~10–12s per thematic query** and reducing prompt token waste.
- **Link & backlink lookups:** Cuts multi-hop connection queries from multiple grep loops (~20–30s) to an instant SQLite edge lookup (<0.1s), saving **~20–25s per graph query**.
- **Duplicate prevention:** Catches existing similar notes during note creation in a single check (<0.2s), avoiding manual duplicate cleanups later.

[[hierarchical map-reduce note rollup]] stays on demand. It is for repeated long-range questions that retrieval and focused reads can't answer.

## Measured state

- 6,567 Markdown notes average 187 body words.
- 1,340 notes (20.4%) have `##` headings. Splitting along headings and 360-token boundaries yields 17,352 chunk sections; 5,225 notes are atomic.
- The largest note is 16,994 words, so sections exceeding 360 tokens are cleanly chunked with overlap.
- 17,352 384-dimension float32 vectors take about 26 MB in memory and execute CPU cosine matmul in <0.5ms.
- The title list is about 33k tokens. Don't put it in an agent prompt; query `note_titles_fts` instead.

## Implemented

[[pkm metadata indexer|index_pkm_meta.py]] provides a local SQLite engine (`.obsidian/pkm_index.db`, ~40 MB) that solves core agent retrieval bottlenecks:

- **FTS5 body & title search:** 17,352 section chunks and 6,567 note titles indexed with Unicode61 full-text search. Replaces broad grep misses with fast BM25 ranking.
- **Resolved link graph:** 22,856 edges indexed with source path, raw target, resolved path, and line numbers. Solves slow multi-hop grep loops with instant 1-hop SQL queries.
- **Neural vector embeddings:** Slices notes into token-bounded sections under `##` headings, embedding them with `BAAI/bge-small-en-v1.5` (384-dim). Solves concept and synonym retrieval where keyword search fails.
- **Per-batch checkpointing:** Commits vectors in 128-item batches directly to SQLite. Solves timeout/token loss by ensuring interrupted runs resume exactly where they left off.
- **Duplicate prevention:** `--check-duplicate` runs cosine similarity against candidate titles before note creation, preventing fragmented note sprawl.
- **Hybrid RRF scoring:** Fuses lexical FTS5 and semantic cosine ranks via Reciprocal Rank Fusion, outputting exact `path:line` targets so agents don't dump full files into prompt context.

## Performance & Build Time Breakdown

Why does the first index build take ~14 minutes? 98% of the time is spent on transformer math across 17,352 sections.

### Where the time goes during initial build

- **File scanning & regex parsing (3s):** Reads 6,567 markdown files from disk, strips YAML frontmatter, extracts 22,856 wikilinks, and chunks 17,352 sections.
- **SQLite FTS5 & graph writes (2s):** Writes the text tables and builds the full-text search index.
- **Neural embedding on CPU (14 min):** 17,352 sections pass through a 12-layer transformer model (`bge-small-en-v1.5`) in ONNX Runtime. On multi-core CPU, throughput is ~20 sections/second ($17,352 / 20 \approx 860\text{s}$).

### Initial build vs runtime queries

- **First build (one-off):** ~14 minutes to compute dense vectors for the entire vault on CPU.
- **Daily incremental updates:** ~2–3 seconds. SHA256 hashes skip unchanged sections, so only edited notes are re-embedded.
- **Search query latency:** <0.5ms. Once vectors are cached, loading the 26 MB matrix and running in-memory dot product cosine similarity (`matrix @ query_vec`) takes less than half a millisecond on CPU.

### Speedup options for initial builds

- **GPU acceleration (DirectML/CUDA):** Verified on [[razor blade 15 rz09-02705w76 2018|Razer Blade 15]] (GTX 1060 6GB) at **764.0 chunks/sec** (1.31s per 1,000 chunks), dropping full vault build time from 14 minutes to **~22 seconds**.
- **Fastembed CPU mode:** Fallback for environments without GPU runtimes, paying the build cost once and using SHA256 incremental cache thereafter.

## Now

### Make the index correct

Don't drop `sections` before reading its hashes. Migrate and upsert rows, then remove only deleted sections. Store section text, or a synchronized FTS5 table, with path, heading, absolute line, content hash, and embedding version. Calculate the line before stripping frontmatter, and log per-file failures instead of swallowing them.

### Chunk for the embedding model

Keep `##` as a boundary, then split long sections into token-bounded chunks with a little overlap and repeated heading context. Give chunks stable identities from path, heading, ordinal, and content hash. The cache key also needs the chunking policy and model version, so only affected rows rebuild.

### Add hybrid retrieval

Use FTS5/BM25 for exact candidates and cosine similarity for semantic candidates, then combine ranks with [[reciprocal rank fusion|RRF]]. Return a path, absolute line, heading, score components, and a short local snippet. Keep `rg` as the quick exact tool and fallback when the database is stale.

Test this against a small hand-picked set: identifiers, aliases, concepts without shared terms, and the problem in [[notes fuzzy search]]. Ship only when it improves useful recall over `rg` alone and indexing reports no unhandled failures.

### Keep links and note creation simple

Extract links on the same walk, but store source path, raw target, resolved target when unambiguous, and link location. Filename alone is unsafe when titles repeat. One-hop context is enough for now.

Before creating a note, search a title index and nearby semantic matches. Show the evidence, but don't block creation or impose one similarity threshold; the agent or user decides whether to append, link, merge, or keep a distinct note. For resolving homonyms and suppressing false duplicate merges, see [[anti link RnD]].

## Later

Build an Obsidian MCP server only when an agent needs live panes, tabs, or a plugin command that has no filesystem equivalent. File reads and index queries don't need it.

Run map-reduce only when date or project filtering plus targeted section retrieval still overflows context, or when the same longitudinal question repeats enough to justify a cached rollup.

Use an ANN index such as FAISS or sqlite-vec only when measured in-memory retrieval becomes a bottleneck. At the current density, a million sections is roughly 640k notes, so the trigger should be latency and memory measurements rather than note count alone.

## References
- [[anti link RnD]]
- [[cross-agent session indexing architecture]]
- [[pkm metadata indexer]]
- [[vault hybrid search]]
- [[multi-repo agentic search architecture]]
