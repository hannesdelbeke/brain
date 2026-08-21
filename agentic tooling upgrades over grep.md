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

Look for these everyday friction points to know when to pull an upgrade off the shelf:

- **Semantic search (Phase 1 — vector embeddings):**
  You search by concept, mood, or vague memory (e.g. *"notes where I felt stuck on projects"*), but the agent keeps guessing synonyms, asks you for the exact title, or fails to find it because the note used different wording.

- **Graph traversal (multi-hop links):**
  You ask *"how are these two topics connected?"* or *"find notes linking to topic A and B"*, and the agent gets stuck in a slow loop: opening a note, grepping its links, opening the next note, and grepping again.

- **Obsidian MCP server (native app API):**
  The agent trips over Windows terminal syntax, path escaping, or needs to interact with Obsidian directly (triggering plugin commands, checking active workspace tabs, or live note state).

- **Map-reduce rollups (batch synthesis):**
  You ask for big-picture historical overviews across hundreds of daily notes (e.g. *"summarize how my focus shifted over 3 years"*), and loading all the raw notes blows past context limits or costs too much.
