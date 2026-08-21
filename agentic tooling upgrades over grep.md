---
tags:
  - ai
  - tools
  - pkm
  - optimization
---
> [!summary] Action Plan
> **Active Implementation (Phased):**
> - **Now (Fuzzy / Thematic Search):** Add lightweight local GPU vector embeddings (`all-MiniLM-L6-v2`) with incremental caching into the SQLite indexer. Eliminates iterative agent guessing on vague queries.
>   - **Time Savings:** Reduces fuzzy search from 2–3 agent turns (~15s) to 1 turn (~4s), saving **~10–12s per thematic query** and cutting token spend.
> - **Later (As Vault Scales):** Native graph traversal, Obsidian MCP server, and recursive map-reduce rollups remain deferred until vault size or multi-hop agent complexity demands them.

While native CLI tools like `grep` are fast for exact string matches (~5–25ms), they struggle with fuzzy, thematic, or "vibe" queries. Grep forces an agent into 2–3 iterative synonym guesses, wasting 10–15 seconds and hundreds of tokens per conceptual lookup.

## Upgrade Roadmap

### Phase 1: What to do Now

#### 1. Incremental GPU Semantic Search (Fast ROI)
- **The Problem:** Queries based on theme or mood (e.g., "times I felt overwhelmed by side projects") fail under literal grep, forcing multiple conversational retries.
- **The Fix:** Add a vector table with incremental SHA256 caching directly into the SQLite metadata indexer (`_scripts/index_pkm_meta.py`) using a small GPU model (`all-MiniLM-L6-v2`).
- **Time & Token Savings:**
  - **Query latency:** 15s (multi-turn guessing) $\rightarrow$ 3–4s (single-turn semantic match). Saves **~10–12s per search**.
  - **Token efficiency:** Eliminates 2–3 redundant prompt roundtrips.
- **Related:** [[vault hybrid search]], [[offline GPU embeddings with incremental cache]], [[pkm metadata indexer]]

---

### Phase 2: What to do Later (Deferred)

#### 2. Native Graph Traversal
- **When to build:** When agents frequently need multi-hop link relationships ($N=2$) or orphan detection without grepping backlink text.
- **Related:** [[vault graph traversal]]

#### 3. Obsidian MCP Server
- **When to build:** When CLI tools or python scripts become too limiting and direct Obsidian app UI/API controls are required.
- **Related:** [[vault MCP server for agents]]

#### 4. Hierarchical Map-Reduce Rollup
- **When to build:** When synthesizing longitudinal multi-year trends over 10k+ daily notes exceeding prompt context windows.
- **Related:** [[hierarchical map-reduce note rollup]], [[token efficient PKM analysis architecture]]

## How to Know When an Upgrade is Needed

- **Semantic search (Phase 1):** Agent runs 2+ consecutive grep attempts trying synonyms, asks for the exact note title, or fails to find notes asked by vibe, theme, or feeling.
- **Graph traversal:** Agent loops reading notes and grepping their backlinks just to map 2-hop connections or find common links between two topics.
- **MCP server:** Agent hits shell or path escaping errors running bash commands, or needs live Obsidian workspace state and plugin interactions.
- **Map-reduce rollup:** Longitudinal timeline requests over years of daily notes blow past context limits or cost excessive prompt tokens.
