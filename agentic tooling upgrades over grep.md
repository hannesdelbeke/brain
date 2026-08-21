---
tags:
  - ai
  - tools
  - pkm
  - optimization
---
> [!summary] Action Plan (Vault Review & Roadmap)
> **Active Implementation (Phased):**
> - **Now (Hybrid Search & Graph Index):** Extend the [[pkm metadata indexer]] with section-level embeddings (`bge-small-en-v1.5`, split on `^## `) and an `edges(src, dst)` link table on the same walk. Query via in-memory CPU `matmul` (~17 MB for ~11k sections, <0.2ms) without external vector databases.
>   - **Core Benefit:** Bridges [[semantic search]] and [[notes fuzzy search]] gaps, fixing grep recall failure at scale (e.g. `agent` matching 40% of the vault vs synonym mismatch returning 0).
>   - **Write-path Protection:** Searches candidate titles before note creation to prevent near-duplicate note sprawl.
> - **Later (On-Demand Triggers):** Obsidian MCP server (triggered only by live workspace UI state) and on-demand map-reduce rollups (fan-out subagents cached on repeat requests).

At scale (5k–10k+ notes), literal `grep` fails on recall in both directions: broad terms match thousands of files (e.g. `agent` matching 40% of notes), while thematic or synonym queries return zero. Injecting raw title lists also breaks (~38k tokens today, passing 50k at 10k notes). 

Upgrading the vault search index requires getting row granularity and query architecture right.

## Vault Empirical Measurements (August 2026)

Checking this architecture against our actual 6,572-note vault yields clear baselines:
- **Mean note size:** 188 words (~250 tokens).
- **Heading distribution:** 68.5% (4,502 notes) are atomic notes without `##` headings; 31.5% (2,070 notes) contain multiple sections (with outliers up to 16k words).
- **Section total:** ~11,000 total sections across the vault.
- **In-memory matrix:** 11,000 sections at 384 dimensions (float32) takes only **~17 MB RAM**, executing numpy `matmul` in **< 0.2ms on CPU**.

## Upgrade Roadmap

### Phase 1: What to do Now

#### 1. Heading-Level Section Embeddings (`^## `)
- **Granularity:** Notes with `##` headings split on `^## ` (~288 tokens/section). Atomic notes without headings (68.5% of vault) are indexed as a single section using the note title as heading (~250 tokens).
- **Model Choice:** Use `bge-small-en-v1.5` (512-token context window, 384 dimensions). This comfortably holds our mean note/section size while preventing truncation on longer sections.
- **Section-Level SHA256:** Key `sections(path, heading, start_line, sha256, vector)` by section content hash so editing one heading re-embeds only that section, not the whole note.
- *Simple explanation: Instead of reading a whole note at once, the system slices it into bite-sized chunks under each heading. This lets you pinpoint the exact paragraph you need without loading the rest of the page.*
- **Related:** [[vault hybrid search]], [[offline GPU embeddings with incremental cache]], [[pkm metadata indexer]], [[semantic search]]

#### 2. In-Memory CPU Matmul (No Vector DB)
- **Architecture:** Load the ~17 MB vector matrix directly into memory and run a single numpy `matmul` (`sims = mat @ query_vec`) in **< 0.2ms on CPU**.
- **Simplicity:** No FAISS, sqlite-vec, or background GPU daemons needed until ~1M sections (~300k notes). GPU is used solely for one-time bulk indexing.
- *Simple explanation: The index is so small that standard computer memory compares meanings instantly, without needing bulky database software.*
- **Related:** [[single-repo vs multi-repo agent search]]

#### 3. Return Locations and Keep Grep
- **Snippet Output:** Search returns `path`, `line_number`, and `heading` (~150 tokens total), never raw note bodies. The agent reads target sections using standard line offsets without wasting context.
- **Hybrid Fusion:** Union exact grep (for names, commit hashes, code identifiers, tags) with cosine vector matches.
- *Simple explanation: Search gives you a page and line number instead of reciting the whole book. We keep exact word search for code and names, and use smart meaning-based search for general topics.*
- **Related:** [[notes fuzzy search]]

#### 4. Extract Link Graph on the Same Walk
- **Free Graph Index:** Because the indexing pass already reads every file body, extracting `[[wikilinks]]` into an `edges(src, dst)` table costs ~10 lines of code with zero marginal crawl overhead.
- **Enables:** Instant multi-hop graph traversal and orphan detection via recursive SQL queries without running multiple agent grep loops.
- *Simple explanation: While indexing the notes, we also sketch a quick roadmap of which notes link to each other, giving us an instant connection map for almost zero extra effort.*
- **Related:** [[vault graph traversal]]

#### 5. Duplicate Prevention on Write Path
- **The Problem:** Near-duplicate note pairs scale quadratically with note count when agents lack cross-session memory.
- **The Fix:** Embed candidate note titles before creation to search nearest neighbors, prompting the agent to append to existing notes rather than creating fragmented duplicates.
- *Simple explanation: Before creating a new note, the system checks if you already wrote something similar in the past so you can update the old note instead of cluttering the vault with duplicates.*

---

### Phase 2: What to do Later (Deferred)

#### 6. Obsidian MCP Server
- **When to build:** Only when tasks require live Obsidian workspace state (active tab, open pane context, triggering plugin commands with no filesystem equivalent).
- **Not for:** Shell errors or file reading (handled cleaner via Python scripts).
- *Simple explanation: A direct remote control for Obsidian. Only needed if an AI assistant needs to click buttons inside the app or see which note tab you currently have open.*
- **Related:** [[vault MCP server for agents]]

#### 7. On-Demand Map-Reduce Rollup
- **When to build:** Run on demand with parallel subagents over date-filtered SQLite sets for longitudinal multi-year queries. Cache date ranges only after being queried repeatedly, avoiding expensive unread precomputed rollups.
- *Simple explanation: For giant questions covering years of daily entries, helper assistants split the years up, summarize each year, and hand a compact summary back to the main assistant.*
- **Related:** [[hierarchical map-reduce note rollup]], [[token efficient PKM analysis architecture]], [[multi-repo agent search cost and ROI]]

---

## Countable Triggers for Upgrades

- **Semantic Section Index:** A common search term matches > 50 files, or full vault title listing exceeds 50k tokens (currently at ~38k tokens).  
  *Simple explanation: When searching a word brings up way too many files, or when listing all note titles becomes too long for memory.*
- **Edges Table:** Built simultaneously on Phase 1 walk (zero marginal cost).  
  *Simple explanation: Built right away because it takes almost no extra work during the initial scan.*
- **Obsidian MCP Server:** An agent workflow explicitly requires live Obsidian UI/workspace context.  
  *Simple explanation: When an assistant actually needs to control the Obsidian app window, not just edit files.*
- **Map-Reduce Rollups:** A longitudinal multi-year query fails date-filtered fan-out or overflows prompt context limits.  
  *Simple explanation: When a big multi-year overview contains too much text to fit in a single prompt.*
- **ANN Vector Index (FAISS/sqlite-vec):** Total section count exceeds 1,000,000 (~300k notes).  
  *Simple explanation: When you have hundreds of thousands of notes and basic in-memory math starts to lag.*
