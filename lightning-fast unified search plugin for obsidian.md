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
Architectural blueprint for building an ultra-fast, zero-lag Obsidian plugin combining exact text search, sub-millisecond fuzzy matching, and local AI vector retrieval across 10,000+ notes.

## Architecture Overview

```
                      ┌──────────────────────────────────────────┐
                      │    Unified Command Palette (Ctrl+K)      │
                      │  Input: "query" | "/regex" | "?semantic" │
                      └────────────────────┬─────────────────────┘
                                           │
                                           ▼
                      ┌──────────────────────────────────────────┐
                      │      Dedicated Web Worker (Non-UI)       │
                      └─────┬──────────────────┬─────────────────┘
                            │                  │
               ┌────────────┴────────┐   ┌─────┴────────────────┐
               ▼                     ▼   ▼                      ▼
    ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
    │   Exact & Regex      │  │  Nucleo / FZF Fuzzy  │  │ Local SQLite Vectors │
    │   (FTS5 / Tantivy)   │  │   Engine (Wasm)      │  │ (bge-small / SIMD)   │
    └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
               │                         │                         │
               └────────────────────┬────┴─────────────────────────┘
                                    ▼
                      ┌───────────────────────────┐
                      │ Merged Top Results (<5ms) │
                      │ Rendered in Obsidian UI   │
                      └───────────────────────────┘
```

## Triple-Engine Search Stack

### High-Precision Fuzzy Search (Nucleo / FZF Wasm)
- **Engine:** `nucleo-matcher` (the Rust engine powering Helix and modern Neovim pickers) compiled to WebAssembly.
- **Capability:** Typo-tolerant, camelCase matching (`2026gemin` -> `2026-07-03 Gemini stopped working`), path-aware scoring.
- **Speed:** Instant keystroke evaluation (<1ms across 10,000 note titles).

### Full-Text & Lexical Search (SQLite FTS5 / MiniSearch)
- **Engine:** Direct read from `.obsidian/pkm_index.db` via SQLite FTS5 (Unicode61) or in-worker `MiniSearch`.
- **Capability:** Boolean operators (`AND`, `OR`, `NOT`), prefix matching, field-specific queries (`tag:work`, `path:projects`).
- **Speed:** Full-text candidate retrieval across 17,000+ chunks in 1–3ms.

### Offline Semantic Vector Search (DirectML GPU / SIMD Float32)
- **Engine:** Vector embeddings generated via `bge-small-en-v1.5` (DirectML GPU background worker per [[offline GPU embeddings with incremental cache]]) and cached in `.obsidian/pkm_index.db`.
- **Capability:** Conceptual search (e.g. searching *"shoulder pain after gym"* retrieves clinical letters and physiotherapy logs without exact keyword overlap).
- **In-Memory Query:** Float32Array dot-product matrix multiplication across 17k vectors in <0.5ms.

## Plugin Implementation Plan

### Phase 1: Core Worker & Incremental Indexer
1. **Background Thread Isolation:** Move all parsing, tokenization, and vector math into a dedicated `Worker()`. The main Obsidian UI thread never handles raw file parsing.
2. **Incremental Cache (SHA256):** Store mtime/content hashes. On vault open, only index modified files (takes <0.1s on startup).
3. **Ignore Pattern Support:** Respect `.obsidian/app.json` ignore filters (`**/.git/**`, `.smart-env/**`, `.trash/**`) as detailed in [[obsidian search and index slow on 5k notes]].
4. **Staleness Banners:** Follow the [[codegraph review|CodeGraph]] pattern: inject an in-band ⚠️ banner when a file was modified within the last debounce window so the user knows live content is updating.

### Phase 2: Unified Search Modal (Svelte / Vanilla DOM)
1. Single hotkey (`Ctrl + K` or `Ctrl + Shift + F`).
2. Mode Prefixes:
   - Default: Smart hybrid (Fuzzy title + BM25 snippet match fused via [[vault hybrid search|RRF]]).
   - `/`: Exact Regex search.
   - `?` or `~`: Semantic Vector search.
   - `#`: Instant Tag filter.
   - `@`: Date / Daily note jump.
3. Top-K Pre-Filtering: Pre-filter the top 500 candidates from each modality before rank fusion to avoid $O(N \log N)$ sorting bottlenecks at 10k–50k note scale.

### Phase 3: Live Backend Synchronization
1. Hook into Obsidian's `vault.on('modify')` and `vault.on('delete')` events.
2. Share the underlying `.obsidian/pkm_index.db` with [[pkm metadata indexer]] so external agent CLI runs and in-editor searches use the exact same unified index.

## Comparison vs Existing Plugins

| Feature | Proposed Unified Engine | Native Obsidian Search | Omnisearch | Smart Connections |
| :--- | :---: | :---: | :---: | :---: |
| **Worker Thread (0 UI Lag)** | ✅ Yes | ❌ Main UI Thread | ⚠️ Partial | ❌ Main Thread |
| **Sub-ms Fuzzy Matching** | ✅ Yes (Nucleo Wasm) | ❌ Basic substring | ❌ Levenshtein only | ❌ None |
| **Local AI Embeddings** | ✅ Yes (Incremental GPU) | ❌ None | ⚠️ Web/Ollama | ✅ Yes (Heavy) |
| **Memory Footprint** | **~25 MB** | ~50 MB | ~120 MB | ~200+ MB |
| **Startup Delay** | **0 ms** (Deferred) | Core | ~500–1500 ms | ~1000–3000 ms |

## References
- Core indexer backend: [[pkm metadata indexer]], [[PKM indexer performance log]]
- Hybrid search architecture: [[vault hybrid search]], [[agentic tooling upgrades over grep]]
- Performance & exclusions: [[obsidian search and index slow on 5k notes]], [[Obsidian Windows Defender exclusion]], [[Obsidian faster startup]]
- Architecture review: [[codegraph review]]
