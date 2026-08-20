---
tags:
  - ai
  - tools
  - cli
  - pkm
  - graph
---
An external CLI graph and retrieval engine for [[AI agent|AI agents]] operating on a Markdown vault with [[wikilink|wikilinks]].

## Beyond Ripgrep
Currently, coding and PKM agents locate notes using simple ripgrep pattern matching and file listing. While fast for exact keywords, this approach fails on three fronts:
- **Zero graph awareness:** Cannot follow 2-hop conceptual neighborhoods, backlinks, or parent Map of Content (MOC) hierarchies without multiple manual round-trips.
- **Synonym & concept blindness:** Misses relevant notes when the query uses different terminology (e.g. searching "sleep latency" misses notes titled "insomnia").
- **High context token waste:** Grep dumps entire files or raw snippets into the agent's context window instead of rank-ordered semantic chunks.

## Core Architecture

**1. Explicit Graph Layer (SQLite)**
Parses all `[[wikilinks]]` and frontmatter relationships into a lightweight SQLite database:
- Tables: `notes`, `links (source, target, link_type, commit_date)`, `tags`.
- Enables instant multi-hop queries (`SELECT target FROM links WHERE source = ?`).

**2. Lexical Search Layer (SQLite FTS5 / BM25)**
Full-text search indexing with BM25 ranking for exact keyword matches, code symbols, acronyms, and file titles.

**3. Semantic Vector Layer**
Embeds note chunks using local sentence-transformers models on GPU, with persistent hashing per [[offline GPU embeddings with incremental cache]] to only process modified files.

**4. Hybrid Retrieval (RRF)**
Combines BM25 lexical scores with cosine embedding similarity using Reciprocal Rank Fusion (RRF) to return balanced results across both exact terms and conceptual matches.

## Agent CLI Interface

```bash
# Retrieve 2-hop neighborhood and relevant context for a note
vault-graph context "wikilink temporal integrity" --depth 2

# Hybrid semantic + keyword search with token budget
vault-graph query "how do agents preserve provenance" --max-tokens 1500

# Shortest connection path between two separate ideas
vault-graph path "2026-04 stroke" "productivity on society"

# Identify unlinked or isolated notes
vault-graph orphans --submodule public
```

### Related
- [[extract historic wikilinks from git]] — Mining link additions and deletions across Git revisions into SQLite.
- [[token efficient PKM analysis architecture]] — Compressing graph nodes and text chunks before feeding LLM contexts.