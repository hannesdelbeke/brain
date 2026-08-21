---
tags:
  - ai
  - tools
  - pkm
  - optimization
---
While native CLI tools like `grep` are fast for exact string matches, they are highly inefficient for [[AI agent|AI agents]] navigating a large [[Personal Knowledge Management|PKM]] vault. `grep` forces the agent into iterative guessing, wasting API tokens and execution time. 

To maximize an agent's speed and context efficiency, we need tools that understand meaning, relationships, and structure rather than just raw text.

## Recommended Upgrades

### 1. Semantic / Hybrid Search (RRF)
- **The Problem with Grep:** It is strictly lexical. If a prompt asks for "AI exhaustion" but the note uses "LLM burnout", `grep` fails, forcing the agent to waste time querying multiple synonyms.
- **The Solution:** A native tool that queries a local vector database. Calling a semantic search tool retrieves the correct note on the first try based on meaning.
- **Related:** [[vault hybrid search]], [[offline GPU embeddings with incremental cache]]

### 2. Native Graph Traversal
- **The Problem with Grep:** `grep` treats the vault as isolated text files. To traverse concepts, the agent must grep a file, read its links, and then run new greps for those links.
- **The Solution:** Expose Obsidian's graph directly via a tool (e.g., `get_neighborhood(note_name, depth=2)`). This pulls all related notes in a single tool call without regex fumbling.
- **Related:** [[vault graph traversal]]

### 3. Repository Maps (`llms.txt`)
- **The Problem with Grep:** Agents lack spatial awareness of the vault. They must use blind directory listings or greps to figure out where things are, wasting early conversational turns.
- **The Solution:** Provide a highly compressed map of the vault (filenames + 1-sentence summaries). An agent reading a map can immediately pinpoint the exact files it needs.
- **Related:** [[agent-friendly documentation tools]], [[multi-repo agentic search architecture]]

### 4. Obsidian MCP Server
- **The Problem with Grep:** Agents have to pretend to be Linux users running bash commands, leading to brittle text parsing and errors.
- **The Solution:** An MCP (Model Context Protocol) Server for Obsidian. This replaces raw bash commands with structured, native API tools like `search_vault()`, `append_to_daily_note()`, or `get_tags()`.
- **Related:** [[vault MCP server for agents]]
