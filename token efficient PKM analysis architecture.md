---
tags:
  - ai
  - pkm
  - architecture
  - technical
  - optimization
origin-sha: 062084521
---
> [!summary] Conclusion
> **Partially implemented.** Flat SQLite metadata indexing is live via the [[pkm metadata indexer]], but complex vector caching and hierarchical map-reduce rollups are not needed right now. A flat structure remains sufficient for the current vault size.

An agent-native architecture for indexing, searching, and synthesizing 10,000+ Markdown notes with minimal API token consumption.

## The Architecture Blueprint

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Storage & Index                    │
│   - SQLite Metadata (`_scripts/index_pkm_meta.py`)          │
│   - Persistent GPU Vector Cache (`nomic` / `bge-m3`)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    [ Real-Time Agent Retrieval ]   [ Batch Multi-Year Rollups ]
    - [[vault graph traversal]]     - [[hierarchical map-reduce note rollup]]
    - [[vault hybrid search]]       - Zero-token SQL pre-filtering
    - [[vault MCP server for agents]] - Macro trajectory analysis
```

## Core Subsystems

**1. [[vault graph traversal|Graph Traversal Layer]]**
Treats `[[wikilinks]]` as a directed network. Provides instant multi-hop neighborhood queries ($N=2$), shortest reasoning paths, and orphan detection.

**2. [[vault hybrid search|Hybrid Search Layer]]**
Combines exact SQLite FTS5 (BM25) keyword matching with local GPU vector embeddings using Reciprocal Rank Fusion (RRF) to resolve both technical identifiers and conceptual synonyms.

**3. [[vault MCP server for agents|Agent Interface (MCP)]]**
Exposes structured retrieval tools (`search_notes`, `get_neighborhood`, `read_section`) directly to AI assistants, eliminating context window waste from raw file dumps.

**4. [[hierarchical map-reduce note rollup|Hierarchical Map-Reduce Rollup]]**
Compresses years of daily notes through multi-stage summaries (Daily $\rightarrow$ Monthly $\rightarrow$ Multi-Year), analyzing decades of logs for under $0.20.

### Related
- [[ai overview app]] — High-level application architecture for automated personal overviews.
- [[offline GPU embeddings with incremental cache]] — Local vector cache mechanics on RTX GPUs.
