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
- **Synonym & concept blindness:** Misses relevant notes when the query uses different terminology (e.g. searching "sleep latency" misses notes titled "insomnia"). [[Obsidian aliases]]
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

## Existing Open Source Tools

### Obsidian MCP Servers
Solves **high context token waste** by replacing raw ripgrep dumps with structured tool calls. Agents query notes, retrieve backlinks, or read specific sections on demand rather than loading entire raw files into context.

- [cyanheads/obsidian-mcp-server](https://github.com/cyanheads/obsidian-mcp-server) — Production MCP server for reading, writing, and searching vault notes directly from AI assistants (Claude, Antigravity, Cursor).
- [StevenStavrakis/obsidian-mcp](https://github.com/StevenStavrakis/obsidian-mcp) — Lightweight standalone MCP server operating directly on the local Markdown filesystem without needing the Obsidian app running.
- [coddingtonbear/obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api) — Exposes Obsidian vault operations via local HTTPS REST API and MCP endpoints.

### Graph Analysis & Semantic Tools
Solves **zero graph awareness** and **synonym blindness**. Graph analyzers compute PageRank, bridge nodes, and 2-hop clusters across wikilinks, while embedding tools match related concepts even when exact keywords or [[Obsidian aliases|aliases]] differ.

- [SkepticMystic/graph-analysis](https://github.com/SkepticMystic/graph-analysis) — Advanced graph-theory metrics for Obsidian wikilinks (PageRank, betweenness centrality, community clustering, bridge nodes).
- [khoj-ai/khoj](https://github.com/khoj-ai/khoj) — Local-first AI personal search assistant indexing markdown notes with offline embeddings and CLI/API query endpoints.
- [brianpetro/obsidian-smart-connections](https://github.com/brianpetro/obsidian-smart-connections) — Real-time local vector embeddings for semantic neighbor retrieval across note chunks.

### Custom Python Blueprint
Solves **all three problems** in a lightweight, single-script CLI without external server dependencies. It combines in-memory graph traversal with fast SQLite BM25 and GPU-cached vector embeddings.

- Graph traversal: `networkx` parsing `\[\[([^\]|#]+)\]\]` for fast shortest path, centrality, and 2-hop neighborhoods.
- Full-text search: Standard library `sqlite3` with `FTS5` (BM25).
- Semantic search: `sentence-transformers` on GPU with persistent hash caching per [[offline GPU embeddings with incremental cache]].

### Related
- [[extract historic wikilinks from git]] — Mining link additions and deletions across Git revisions into SQLite.
- [[token efficient PKM analysis architecture]] — Compressing graph nodes and text chunks before feeding LLM contexts.
