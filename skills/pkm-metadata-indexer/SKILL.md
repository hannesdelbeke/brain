---
name: pkm-metadata-indexer
description: Fast local metadata, neural section embeddings, link graph, and hybrid search for Markdown notes in SQLite.
aliases:
  - pkm metadata indexer
  - pkm-metadata-indexer
origin-sha: "062084521"
created: 2026-08-20
tags:
  - technical
  - pkm
  - skill
---

Fast local metadata, neural section embedding, link graph, and hybrid search tool for Markdown notes. 

Parses frontmatter, heading-level sections (`^## `), wikilinks, and vector embeddings (`bge-small-en-v1.5`) directly into a local SQLite database (`.obsidian/pkm_index.db`).

## Commands & Usage

### 1. Build / Update Index
Scans the vault, caches frontmatter, extracts wikilink edges, and embeds new or modified sections:
```bash
python public/skills/pkm-metadata-indexer/index_pkm_meta.py
# Fast build skipping neural embeddings (metadata + links only):
python public/skills/pkm-metadata-indexer/index_pkm_meta.py --skip-embeddings
```

### 2. Fast Semantic Search Tool
Run fast CLI semantic search directly:
```bash
python public/skills/pkm-metadata-indexer/search_vault.py "notes on feeling overwhelmed by projects"
```

### 3. In-Indexer Hybrid Search
Searches vault sections using combined lexical matching and neural vector cosine similarity (via in-memory GPU/CPU matrix multiplication):
```bash
python public/skills/pkm-metadata-indexer/index_pkm_meta.py --search "notes on feeling overwhelmed by projects"
```

### 3. Duplicate Note Prevention
Checks for semantic overlap before creating a new note to prevent note sprawl:
```bash
python public/skills/pkm-metadata-indexer/index_pkm_meta.py --check-duplicate "Obsidian link graph complexity"
```

### 4. Link Graph Queries
Instant lookup of inbound backlinks and outbound connections:
```bash
python public/skills/pkm-metadata-indexer/index_pkm_meta.py --links "Obsidian"
```

### 5. Index Stats
View database size, note count, indexed sections, and graph edge counts:
```bash
python public/skills/pkm-metadata-indexer/index_pkm_meta.py --stats
```

## What it extracts
- **Frontmatter metadata:** energy, sentiment, sentiment_labels, tags.
- **Heading-Level Sections:** Sections split by `## ` with line numbers and SHA256 hashes for incremental caching.
- **Neural Embeddings:** 384-dimensional dense vectors (`BAAI/bge-small-en-v1.5`) stored as float32 blobs.
- **Link Graph (`edges`):** All source-to-target `[[wikilinks]]` for instant traversal without grepping files.

## Why use this
Enables instant SQL aggregations and single-turn semantic search across thousands of notes with zero ongoing API costs, serving as an intelligent pre-filter for agents.

### Related
- [[agentic tooling upgrades over grep]]
- [[vault hybrid search]]
- [[offline GPU embeddings with incremental cache]]
- [[vault graph traversal]]
- [[token efficient PKM analysis architecture]]
