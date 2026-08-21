---
tags:
  - ai
  - tools
  - pkm
  - optimization
---
> [!summary] Plan
> Finish the local index before relying on semantic search. The metadata and link index exists, but the active database has no section rows or embeddings, and no FTS5 body index. Keep `rg` for exact retrieval; add local semantic retrieval for themes and synonyms.

Increase agent reply speed and context efficiency across the vault by upgrading from literal `grep` to meaning-based semantic search and link graph traversal.

## Expected Time Savings

- **Thematic & fuzzy search:** Cuts multi-turn synonym guessing (15s over 2–3 agent turns) to a single turn (~3–4s), saving **~10–12s per thematic query** and reducing prompt token waste.
- **Link & backlink lookups:** Cuts multi-hop connection queries from multiple grep loops (~20–30s) to an instant SQLite edge lookup (<0.1s), saving **~20–25s per graph query**.
- **Duplicate prevention:** Catches existing similar notes during note creation in a single check (<0.2s), avoiding manual duplicate cleanups later.

[[hierarchical map-reduce note rollup]] stays on demand. It is for repeated long-range questions that retrieval and focused reads can't answer.

## Measured state

- 6,565 Markdown notes average 187 body words.
- 1,340 notes (20.4%) have `##` headings. The current splitter yields 10,231 non-empty sections; 5,225 notes are atomic.
- The largest note is 16,994 words, so headings alone don't keep sections within the 512-token embedding limit.
- 10,231 384-dimension float32 vectors take about 15 MB. Benchmark the whole query path, not just matrix scoring.
- `agent` appears in 184 notes (2.8%). Use measured broad queries, not this term, to demonstrate grep overload.
- The title list is about 33k tokens by a rough character estimate. Don't put it in an agent prompt.

## Implemented

`public/skills/pkm-metadata-indexer/index_pkm_meta.py` and the [[pkm metadata indexer|metadata-indexer skill]] already parse selected frontmatter and wikilinks, and expose index, search, duplicate-check, link-query, and stats commands.

`.obsidian/pkm_index.db` is 33.04 MB and currently holds 6,565 notes and 21,061 link edges. The script has code paths for `bge-small-en-v1.5`, cosine search, RRF, and duplicate checks, but the database reports 0 sections and 0 embeddings. Its lexical branch only searches paths and headings with `LIKE`; FTS5/BM25 body search is not built yet.

The existing edge table is enough for inbound and outbound links. Keep multi-hop paths, centrality, and orphan reports deferred until they serve a repeated task.

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

Before creating a note, search a title index and nearby semantic matches. Show the evidence, but don't block creation or impose one similarity threshold; the agent or user decides whether to append, link, merge, or keep a distinct note.

## Later

Build an Obsidian MCP server only when an agent needs live panes, tabs, or a plugin command that has no filesystem equivalent. File reads and index queries don't need it.

Run map-reduce only when date or project filtering plus targeted section retrieval still overflows context, or when the same longitudinal question repeats enough to justify a cached rollup.

Use an ANN index such as FAISS or sqlite-vec only when measured in-memory retrieval becomes a bottleneck. At the current density, a million sections is roughly 640k notes, so the trigger should be latency and memory measurements rather than note count alone.
