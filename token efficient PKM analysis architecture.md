---
tags:
  - ai
  - pkm
  - architecture
  - technical
  - optimization
  - ai-generated
---
Strategies and architectures to analyze 10,000+ Obsidian notes using [[large language model|LLMs]] without incurring high API token costs.
- graph, to search efficiently
- GPU vector search, to search by meaning
- summaries for high level overview

## The Problem
Feeding thousands of raw markdown files directly into frontier LLM context windows burns millions of tokens on boilerplate, YAML frontmatter, and formatting noise.

---

## The 3-tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Level 1: Local Filter & Index             │
│       Strip YAML, junk files, extract metadata into SQLite  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Level 2: Incremental GPU Embeddings         │
│        Chunk notes locally using cached vector database     │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Level 3: Hierarchical Map-Reduce Rollup        │
│   Days (local) ──► Month Summaries ──► Year Meta-Review     │
└─────────────────────────────────────────────────────────────┘
```

### Tier 1: Local SQLite Metadata Index (0 Cost)
- **What was built:** A local Python indexer (`_scripts/index_pkm_meta.py`, documented in [[_scripts/pkm metadata indexer]]) scans the vault and indexes all Markdown notes into `.obsidian/pkm_index.db`.
- **Schema & extracted data:**
  - `path`, `filename`, `category` (daily, review, general)
  - `energy` (int, 1–10)
  - `sentiment` (float) & `sentiment_labels` (JSON array: e.g. `["frustrated"]`, `["focused"]`)
  - `tags` (JSON array: `#work`, `#health`, etc.)
  - `summary_snippet` (first 15 high-signal markdown headers and task items)
  - `word_count`
- **What it enables:** Instant SQL aggregations across years (energy graphs by month, emotion counts, burnout queries) with **zero API tokens**. Useful as a pre-filter before calling LLMs.

### Tier 2: Local GPU Vector Search with Incremental Cache (0 Cost)
- Embeds notes locally using an RTX GPU and open models (`nomic-embed-text`, `bge-m3`, or `all-MiniLM-L6-v2`).
- Uses content hashes / `mtime` so only newly created or modified notes get embedded. Unmodified notes load instantly from cache per [[offline GPU embeddings with incremental cache]].

### Tier 3: Hierarchical Map-Reduce Rollup (< $0.20 Total)
1. **Daily $\rightarrow$ Monthly:** Run a fast, low-cost model (e.g. Gemini Flash / Claude Haiku) over pre-filtered daily summaries (~5k tokens/month = ~60k tokens/year).
2. **Monthly $\rightarrow$ Multi-Year Meta Review:** Send the 12–24 structured monthly summaries to a deep reasoning model (Gemini Pro / Claude Opus) for long-term trajectory patterns (~30k tokens).
