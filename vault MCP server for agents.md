---
tags:
  - ai
  - tools
  - mcp
  - pkm
---
Exposing Markdown vault reading, search, and graph traversal tools to AI assistants via the Model Context Protocol (MCP) to reduce context token waste.

## Why MCP Beats Raw Ripgrep
When AI agents locate notes using simple ripgrep commands, they often load entire multi-thousand-word documents into the prompt context just to find a single paragraph.

An MCP server exposes structured, token-efficient tool primitives:
- `search_notes(query, limit)`: Runs hybrid search and returns ranked note snippets.
- `get_neighborhood(note, depth)`: Returns the 1-hop or 2-hop connected graph cluster.
- `read_section(note, heading)`: Extracts only the relevant section without loading the whole file.

## Implementations
- **[cyanheads/obsidian-mcp-server](https://github.com/cyanheads/obsidian-mcp-server):** Feature-complete production MCP server for reading, writing, and searching vault notes.
- **[StevenStavrakis/obsidian-mcp](https://github.com/StevenStavrakis/obsidian-mcp):** Lightweight standalone server working directly on raw Markdown files without requiring the Obsidian app.
- **[coddingtonbear/obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api):** Exposes Obsidian vault operations via local HTTPS REST API and MCP endpoints.

### Related
- [[vault hybrid search]] — Underlying BM25 + vector search powering MCP query tools.
- [[vault graph traversal]] — Graph algorithm primitives exposed to agents over MCP.
