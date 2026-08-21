---
tags:
  - ai
  - tools
  - pkm
  - optimization
---
> [!summary] Action Plan (10k Notes Scaling)
> **Active Implementation (Phased):**
> - **Now (Hybrid Search & Graph Index):** Extend the [[pkm metadata indexer]] with section-level embeddings (`bge-small-en-v1.5`, split on `^## `) and an `edges(src, dst)` link table on the same walk. Query via in-memory CPU `matmul` (104 MB for 68k sections, <1ms) without external vector databases.
>   - **Core Benefit:** Fixes grep recall failure at scale (e.g. `agent` matching 40% of the vault vs synonym mismatch returning 0) and eliminates 2–3 iterative guessing turns.
>   - **Write-path Protection:** Searches candidate titles before note creation to prevent near-duplicate note sprawl.
> - **Later (On-Demand Triggers):** Obsidian MCP server (triggered only by live workspace UI state) and on-demand map-reduce rollups (fan-out subagents cached on repeat requests).

At scale (5k–10k+ notes), literal `grep` fails on recall in both directions: broad terms match thousands of files (e.g. `agent` matching 40% of notes), while thematic or synonym queries return zero. Injecting raw title lists also breaks (~109k tokens for 10k notes). 

Upgrading the vault search index requires getting row granularity and query architecture right.

## Upgrade Roadmap

### Phase 1: What to do Now

#### 1. Heading-Level Section Embeddings (`^## `)
- **The Problem with Note-Level Vectors:** Whole notes average ~2,000 tokens. A 256-token embedding model (`all-MiniLM-L6-v2`) silently truncates at ~180 words, discarding 90% of the note body and ruining recall.
- **The Fix:** Split notes on `^## ` section headings (~288 tokens per section, ~6.8 sections per note). Use `bge-small-en-v1.5` (512-token context window, 384 dimensions).
- **Section-Level SHA256:** Key `sections(path, heading, start_line, sha256, vector)` by section content hash so editing one heading re-embeds only that section, not the whole note.
- **Related:** [[vault hybrid search]], [[offline GPU embeddings with incremental cache]], [[pkm metadata indexer]]

#### 2. In-Memory CPU Matmul (No Vector DB)
- **Architecture:** 10,000 notes produces ~68,000 sections. At 384 float32 dimensions, the entire vector matrix is only **104 MB**.
- **Query Path:** Load the matrix into memory and run a single numpy `matmul` (`sims = mat @ query_vec`) in **< 1ms on CPU**. No FAISS, sqlite-vec, or background GPU services needed until ~1M sections (~300k notes). GPU is used solely for one-time bulk indexing.

#### 3. Return Locations and Keep Grep
- **Snippet Output:** Search returns `path`, `line_number`, and `heading` (~150 tokens total), never raw note bodies. The agent reads target sections using standard line offsets without wasting context.
- **Hybrid Fusion:** Union exact grep (for names, commit hashes, code identifiers, tags) with cosine vector matches.

#### 4. Extract Link Graph on the Same Walk
- **Free Graph Index:** Because the indexing pass already reads every file body, extracting `[[wikilinks]]` into an `edges(src, dst)` table costs ~10 lines of code with zero marginal crawl overhead.
- **Enables:** Instant multi-hop graph traversal and orphan detection via recursive SQL queries without running multiple agent grep loops.
- **Related:** [[vault graph traversal]]

#### 5. Duplicate Prevention on Write Path
- **The Problem:** Near-duplicate note pairs scale quadratically with note count when agents lack cross-session memory.
- **The Fix:** Embed candidate note titles before creation to search nearest neighbors, prompting the agent to append to existing notes rather than creating fragmented duplicates.

---

### Phase 2: What to do Later (Deferred)

#### 6. Obsidian MCP Server
- **When to build:** Only when tasks require live Obsidian workspace state (active tab, open pane context, triggering plugin commands with no filesystem equivalent).
- **Not for:** Shell errors or file reading (handled cleaner via Python scripts).
- **Related:** [[vault MCP server for agents]]

#### 7. On-Demand Map-Reduce Rollup
- **When to build:** Run on demand with parallel subagents over date-filtered SQLite sets for longitudinal multi-year queries. Cache date ranges only after being queried repeatedly, avoiding expensive unread precomputed rollups.
- **Related:** [[hierarchical map-reduce note rollup]], [[token efficient PKM analysis architecture]]

## Countable Triggers for Upgrades

- **Semantic Section Index:** A common search term matches > 50 files, or full vault title listing exceeds 50k tokens.
- **Edges Table:** Built simultaneously on Phase 1 walk (zero marginal cost).
- **Obsidian MCP Server:** An agent workflow explicitly requires live Obsidian UI/workspace context.
- **Map-Reduce Rollups:** A longitudinal multi-year query fails date-filtered fan-out or overflows prompt context limits.
- **ANN Vector Index (FAISS/sqlite-vec):** Total section count exceeds 1,000,000 (~300k notes).
