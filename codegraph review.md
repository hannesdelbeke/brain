---
date: 2026-08-24
tags:
  - technical
  - ai
  - tools
  - graph
  - architecture
  - review
---
Review of [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)—a local, pre-indexed code knowledge graph with native AST parsing and auto-sync for AI coding agents—and how it compares to our [[pkm metadata indexer|PKM metadata indexer]] and [[agentic tooling upgrades over grep|agentic search architecture]].

## 1. What CodeGraph Is

CodeGraph is a 100% local code intelligence engine and MCP server designed to eliminate agent discovery loops (ripgrep/globbing/reading one file at a time).

- **Native Rust Kernel & Tree-Sitter:** Compiles tree-sitter grammars directly into a native Rust binary, extracting AST nodes (classes, methods, functions) and edges (calls, imports, inheritance) across 20 languages.
	- *ELI5:* Instead of reading code like plain text, a high-speed engine breaks your code down like LEGO bricks so the AI instantly knows which piece snaps into what.
- **SQLite + FTS5 Storage:** Persists symbols, relationships, and file metadata in `.codegraph/codegraph.db`.
	- *ELI5:* Saves that entire LEGO blueprint into a local, searchable phonebook on your SSD so looking up any function takes less than a millisecond.
- **Cross-Boundary & Framework Resolution:** Resolves dynamic web routes (Django, FastAPI, Express, Spring) and mixed-language native bridges (Swift/Obj-C, React Native native modules).
	- *ELI5:* Connects the dots when a website URL triggers backend code, or when JavaScript talks to native iPhone/Android code without losing the trail.
- **Single-Tool MCP Design (`codegraph_explore`):** Rather than giving agents a fragmented menu of granular tools, it exposes one primary entry point that returns verbatim source, call paths, and blast radius in a single payload.
	- *ELI5:* Gives the AI one all-in-one button that hands over the exact code, who calls it, and what might break in one shot, rather than making the AI ask 20 separate questions.
- **Live Auto-Sync & Staleness Signaling:** Uses native OS file watchers (`ReadDirectoryChangesW`/`inotify`/`FSEvents`) with debounced auto-sync. During the debounce window, it injects a ⚠️ staleness banner so agents know to read modified files directly.
	- *ELI5:* Watches your files while you type and updates the map in the background. If you ask a question before the map finishes saving, it raises a flag saying "check the file directly, I'm still updating!"

## 2. Architecture Comparison: CodeGraph vs Our Solutions

| Dimension | CodeGraph (`colbymchenry/codegraph`) | Our Solution ([[pkm metadata indexer]]) |
| :--- | :--- | :--- |
| **Primary Domain** | Source code ASTs, call graphs, type hierarchies, framework routes | Markdown notes, frontmatter metadata, wikilink graph, natural language concepts |
| **Parsing Engine** | Native Rust kernel with compiled Tree-Sitter grammars | Python parser with heading-based token chunking (`##` boundaries + overlap) |
| **Graph Model** | Symbol-to-symbol call trees, inheritance, imports, route bindings | Note-to-note and section-to-section resolved [[wikilinks]] and backlinks |
| **Search Paradigm** | Deterministic symbol resolution + SQLite FTS5 lexical search | **Hybrid Retrieval:** FTS5 BM25 lexical + `bge-small-en-v1.5` neural vector embeddings (DirectML GPU) fused via [[reciprocal rank fusion|RRF]] |
| **Semantic Concept Matching** | No neural embeddings (purely AST & lexical symbol matching) | **Yes:** Dense vector dot-product matrix (<0.5ms) for thematic similarity and duplicate prevention |
| **Agent Interface** | Single high-density MCP tool (`codegraph_explore`) returning full source + flow | Granular query tools (`search_vault.py`, `check_duplicate`) returning `path:line` targets |
| **File Syncing** | Continuous background daemon with OS watcher & debounce (300ms–2s) | SHA256 diff cache with batch checkpointing (~2s incremental on GPU) |
| **Context Strategy** | Dense verbatim payload in 1 call (fewer turns, higher residual context) | Surgical line-range targets (lower turn context, relies on targeted `view_file`) |

## 3. Key Takeaways & Ideas to Steal

- **Single-Tool MCP Steering:** CodeGraph measured that exposing one comprehensive tool (`codegraph_explore`) resulted in 88% fewer tool calls and prevented agents from picking the wrong narrow tool or spawning wasteful exploratory sub-agents.
- **Explicit Staleness Signaling:** Injecting an in-band ⚠️ banner when a file edit is pending inside the debounce window prevents agent hallucinations between save and re-index.
- **Framework & Route Awareness:** Emitting synthetic route nodes for web handlers and cross-language bridges is a clean pattern for unifying multi-language codebases.
- **Tree-Sitter for Code Snippets in PKM:** Adopting tree-sitter tokenization for code fences inside Markdown notes would fix FTS5 syntax splitting on operators (`=>`, `::`, `<>`).

## 4. Adopted, 2026-08-25

Installed and wired to every agent on this machine. It answers a different question than the [[pkm metadata indexer]] rather than competing with it: that one finds notes by meaning, this one resolves symbols by structure, and neither does the other's job.

Where it earns its keep is large codebases, so the rule is a size and activity threshold rather than everything:

| Repository | Files indexed | Nodes | Edges | Index time | DB |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 618k LOC C# Unity client | 4,853 | 111,463 | 253,840 | 17.4s | 251 MB |
| 305k LOC TypeScript game | 1,241 | 25,092 | 83,783 | 5.2s | 91 MB |
| 145k LOC Python tooling | 426 | 12,290 | 25,873 | 2.0s | — |

Below roughly 15k LOC nothing was indexed. A grep plus a read already answers the question there, and an index is one more thing to keep fresh for no gain.

Setup notes worth keeping:

- `npm i -g @colbymchenry/codegraph`, then `codegraph telemetry off` **before** anything else. It is anonymous by the documented field list, but proprietary work is not the place to find out.
- `codegraph install -y` wires the MCP server into every agent it detects and also appends a block to the global `CLAUDE.md` and an `mcp__codegraph__*` entry to the permission allow-list. Both are reversible and both are worth knowing about rather than discovering later.
- It honours `.gitignore` and skips `node_modules`, `dist`, `target` and friends by default, so a Unity repository indexes its own code and not `Library/`.
- The `.codegraph/` directory holds a database of a few hundred MB. It self-ignores its contents but still shows as untracked, so it belongs in the global excludes file (`~/.config/git/ignore`), not in each repository's `.gitignore` — nothing gets committed to a repository just because a local tool was installed.
- A shell `codegraph explore` takes ~1.7s, most of it process start. The MCP server keeps it resident, which is the same argument the [[lightning-fast unified search plugin for obsidian|search daemon]] makes for the vault.

## References
- Equivalents for Markdown vaults, and what to steal from each: [[pkm vault indexing landscape]]
- [[pkm metadata indexer]]
- [[agentic tooling upgrades over grep]]
- [[PKM indexer performance log]]
- [[semantic index as a git extension]] — where a structural index and a semantic one would sit if both installed into a repo the way `git lfs install` does, and why `.codegraph/` staying local is the norm rather than the exception
