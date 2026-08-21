---
name: pkm-metadata-indexer
description: Fast local metadata and summary extractor for Markdown notes into SQLite
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
Fast local metadata and summary extractor for Markdown notes. Parses YAML frontmatter (energy, sentiment, tags) and top-level headings/task items directly into a SQLite database (`.obsidian/pkm_index.db`).

## How to run
```bash
python skills/pkm-metadata-indexer/index_pkm_meta.py
# or specify a custom vault directory
python skills/pkm-metadata-indexer/index_pkm_meta.py --vault /path/to/vault
```

## What it extracts
- **Frontmatter metadata:** energy, sentiment, sentiment_labels, tags.
- **Structural snippets:** First 15 high-signal headings and markdown checkboxes (`- [ ]`, `- [x]`).
- **Metrics:** Note word count, category (daily, review, work, general), and relative file path.

## Why use this
Enables instant SQL aggregations across thousands of notes (energy trends, burnout queries, emotion counts) with zero API token costs, serving as a lightweight pre-filter before feeding notes to LLMs.

### Related
- [[vault hybrid search]]
- [[offline GPU embeddings with incremental cache]]
- [[token efficient PKM analysis architecture]]
- [[agentic tooling upgrades over grep]]
