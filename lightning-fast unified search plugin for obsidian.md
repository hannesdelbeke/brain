---
date: 2026-08-24
tags:
  - technical
  - obsidian
  - plugin
  - search
  - ai
  - pkm
origin-sha: e14817ef
created: 2026-08-24
---
Architectural blueprint for a decoupled, zero-lag search engine: a standalone local search daemon paired with a lightweight [[Obsidian plugin]] UI modal, terminal CLI, and AI agent MCP server.

**This was built.** The daemon is `skills/pkm-metadata-indexer/searchd.py` and the shape below survived contact; the parts that changed are in [[#What was actually built]] at the bottom, which is the section to trust where the two disagree.

## Architecture Overview

```
                       ┌────────────────────────────────────────────────────────┐
                       │                   Multiple Consumers                   │
                       │                                                        │
                       │  ┌──────────────────┐  ┌────────────────────────────┐  │
                       │  │ Obsidian Plugin  │  │ AI Agents (Claude / AGY)   │  │
                       │  │ (Thin Modal UI)  │  │ (via stdio / MCP Tool)     │  │
                       │  └─────────┬────────┘  └─────────────┬──────────────┘  │
                       │            │                         │                 │
                       │  ┌─────────┴────────┐  ┌─────────────┴──────────────┐  │
                       │  │ System Launcher  │  │ Terminal CLI               │  │
                       │  │ (Raycast/Alfred) │  │ (`pkm search <query>`)     │  │
                       │  └─────────┬────────┘  └─────────────┬──────────────┘  │
                       └────────────┼─────────────────────────┼─────────────────┘
                                    │                         │
                                    ▼                         ▼
                       ┌────────────────────────────────────────────────────────┐
                       │          Local IPC / HTTP API (`127.0.0.1:44771`)      │
                       ├────────────────────────────────────────────────────────┤
                       │             PKM Unified Search Daemon (Core)           │
                       │                                                        │
                       │  • File Watcher (`notify` / incremental SHA256 diff)   │
                       │  • Exact & Boolean Full-Text (SQLite FTS5)             │
                       │  • Sub-ms Fuzzy Title/Path Matcher (Nucleo / FZF)      │
                       │  • Dense Vector Similarity (bge-small / SIMD FP16)     │
                       │  • Reciprocal Rank Fusion (RRF Top-K)                  │
                       │  • Shared DB: `.obsidian/pkm_index.db`                 │
                       └────────────────────────────────────────────────────────┘
```

## Why a Decoupled Service Wins

Monolithic Obsidian plugins bundle heavy runtimes (Wasm, vector stores, Electron file parsers) directly into the editor process, creating UI freezes, startup lag, and siloing search capability inside Obsidian.

A standalone daemon solves this cleanly:

| Dimension | Monolithic Obsidian Plugin | Decoupled Local Daemon + Thin Plugin |
| :--- | :--- | :--- |
| **Consumer Access** | ❌ Only available inside Obsidian. | ✅ Obsidian UI, AI agents (MCP), Raycast/Alfred, Terminal CLI. |
| **Obsidian Startup** | ❌ Adds 500–2,000ms delay to Obsidian load time. | ✅ **0 ms Obsidian impact** (daemon runs independently). |
| **Memory Footprint** | ❌ Bloats Obsidian's Electron renderer process. | ✅ Isolated lightweight process (~20–35 MB RAM in Rust/Go). |
| **Crash Isolation** | ❌ Heavy indexing freezes or crashes Obsidian UI. | ✅ Background crashes/rebuilds never affect editor panes. |
| **AI Agent Synergy** | ❌ Agents cannot search when Obsidian is closed. | ✅ Agents search directly via standard CLI or MCP endpoints. |

## System Components

### 1. Standalone Search Daemon (`pkm-searchd`)
- **Engine Core:** Implemented in Rust (or lightweight Python daemon extending [[pkm metadata indexer]]).
- **Fuzzy Matcher:** In-memory `nucleo-matcher` (powering Helix and modern pickers) for sub-millisecond title and path search.
- **Full-Text Index:** SQLite FTS5 with Unicode61 tokenizer and `PRAGMA journal_mode=WAL;` for zero-lock concurrent reads.
- **Dense Vector Search:** Cached `bge-small-en-v1.5` embeddings per [[offline GPU embeddings with incremental cache]], computing Float32/FP16 cosine similarity across 17,000+ chunks in <1ms.
- **Rank Fusion:** Combines fuzzy, lexical, and vector candidate sets via [[vault hybrid search|Reciprocal Rank Fusion (RRF)]], pre-filtering the top 500 candidates per modality.
- **File Watcher:** Native background watcher (`notify` crate) updating changed notes incrementally on file-save.

### 2. Local IPC & REST API Endpoints
The daemon listens on localhost (`127.0.0.1:44771` or named pipe/Unix socket):
- `GET /search?q=query&mode=hybrid|exact|fuzzy|vector&limit=20`: Returns structured JSON with snippets and match highlights in 1–3ms.
- `GET /links?note=title`: Returns inbound and outbound wikilink graph edges.
- `POST /reindex`: Triggers on-demand incremental vault sync.
- `GET /health`: Daemon status, note count, indexed vectors, and memory stats.

### 3. Thin Obsidian Plugin (~50 KB)
- Pure presentation layer with zero local ML dependencies.
- **Hotkey (`Ctrl + K` or `Ctrl + Shift + F`):** Opens a fast Svelte / Vanilla DOM palette modal.
- **Query Routing:**
  - Default: Hybrid smart search (Fuzzy title + BM25 snippet match).
  - `/`: Exact Regex search.
  - `?` or `~`: Semantic Vector search.
  - `#`: Instant Tag filter.
  - `@`: Date / Daily note jump.
- **Daemon Lifecycle Management:** Checks `GET /health` on startup; if the daemon is not running, launches it as a background detached process.

### 4. External Consumers
- **System-Wide Spotlight Search:** Trigger vault searches from anywhere in the OS via Raycast, Flow Launcher, or PowerToys Run plugins calling `GET /search`.
- **AI Agent MCP Server:** Exposes a unified `pkm_search` tool over Model Context Protocol (MCP) so Claude Code, Antigravity, or Cursor can search the vault effortlessly without parsing raw Markdown trees.

## What was actually built

`searchd.py` plus a thin plugin, both against the existing SQLite index. Where the plan above was wrong or optimistic:

| Planned | Built | Why |
| :--- | :--- | :--- |
| Rust engine, `nucleo-matcher`, `notify` watcher | Python daemon on stdlib `ThreadingHTTPServer` | The work is ONNX C++, SQLite C and BLAS. Python is a few milliseconds of glue around them, so a rewrite buys nothing until the vault is ~10x larger, and then `sqlite-vec` or HNSW beats a language change |
| 1–3ms per query | **13–22ms**, flat | The estimate ignored encoding the query, which is the largest single stage even warm |
| Fuzzy matching in the daemon | In the plugin, via Obsidian's `prepareFuzzySearch` | Titles and tags are already in the editor's metadata cache, so shipping them to a daemon to rank would be slower than ranking them where they sit |
| File watcher, incremental on save | `POST /reindex`, run manually | An incremental run is ~11s and the index is never far behind. Worth adding when that stops being true |
| MCP server for agents | HTTP and `search_vault.py` | Agents can already curl or shell out; MCP is a wrapper to add when an agent needs it as a tool rather than a command |
| One daemon, one vault | One daemon, **many vaults**, `?vault=name` | The resident model is the expensive part and it is vault-independent, so a second daemon per vault pays for it twice |
| Localhost bind is the security model | Loopback `Host` check, any `Origin` refused, optional `X-PKM-Token` | Binding to 127.0.0.1 keeps nothing out: any page the browser visits can POST to it, and DNS rebinding can point a hostile name here |

The modal's prefix routing shipped as planned, with `?` and `~` both meaning semantic: `MODES = { "/": "regex", "?": "semantic", "~": "semantic", "#": "tag", "@": "date" }`, on `Ctrl+Shift+K`. Semantic queries hit the daemon and fall back to the CLI, and the plugin spawns the daemon detached if nothing answers.

A fifth endpoint arrived after this table, `GET /unlinked?note=`, which serves unlinked mentions from the same index and drops the ones the built-in pane gets wrong. It is written up in [[unlinked mentions from the vault index]].

Query cost, and the two measurements that were counter-intuitive, are in [[PKM indexer performance log]].

## References
- Core indexer backend: [[pkm metadata indexer]], [[PKM indexer performance log]]
- Hybrid search architecture: [[vault hybrid search]], [[agentic tooling upgrades over grep]]
- Performance & exclusions: [[obsidian search and index slow on 5k notes]], [[Obsidian Windows Defender exclusion]], [[Obsidian faster startup]]
- Unlinked mentions: [[unlinked mentions from the vault index]]
- Architecture review of a similar tool: [[codegraph review]]
