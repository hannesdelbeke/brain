---
date: 2026-08-29
created: 2026-08-29
tags:
  - architecture
  - search
  - release-plan
  - modularity
  - obsidian
  - pkm
  - agents
aliases:
  - search suite release plan
  - modular search daemon release plan
  - 2026-08-29 local search daemon and indexer - release plan and modular decoupling
---

# 🚀 Local Search Daemon & Indexer Suite: Release Plan & Modular Decoupling

A unified release strategy and architectural blueprint to decouple the **Local Search Daemon & Indexer** into three distinct distribution packages (Core Library, Obsidian Plugin, and Session Searcher), while maintaining strict modular separation between **Header Extraction**, **Lexical Fast Search**, and **Semantic Neural Search**.

Related: [[progress - local-first search daemon and indexer]], [[cross-agent session indexing architecture]], [[core Obsidian features to rework on the vault index]], [[2026-08-27 tail reads, resuming an index at the byte it stopped at|tail reads]], [[2026-08-18 what retrieval costs as a vault grows|retrieval economics]], [[2026-08-29 agentic memory - scoped devlogs vs monolithic memory|scoped agent memory]]

---

## 🧩 Architectural Decoupling: Separating the 3 Core Search Primitives

Can **Header Extraction**, **Super Fast Lexical Search**, and **Semantic Vector Search** remain completely independent modules? **Yes, and they should be.**

```
                               ┌────────────────────────────────────────┐
                               │           RAW TEXT / MARKDOWN          │
                               └───────────────────┬────────────────────┘
                                                   │
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │       1. HEADER / CHUNK EXTRACTOR      │
                               │           (Pure AST Parser)            │
                               │  • Zero dependencies, <1ms execution   │
                               │  • Splits on ## headings + line ranges │
                               │  • Generates section SHA256 hashes     │
                               └───────────────────┬────────────────────┘
                                                   │
                   ┌───────────────────────────────┴───────────────────────────────┐
                   ▼                                                               ▼
    ┌───────────────────────────────┐                               ┌───────────────────────────────┐
    │    2. SUPER FAST SEARCH       │                               │     3. SEMANTIC SEARCH        │
    │      (Lexical Engine)         │                               │       (Vector Engine)         │
    │  • SQLite FTS5 / BM25         │                               │  • ONNX + DirectML / CPU      │
    │  • Exact words, code symbols  │                               │  • bge-small-en-v1.5 vectors  │
    │  • 0MB vector memory overhead │                               │  • In-memory NumPy dot product│
    │  • Instant 0ms cold-start     │                               │  • Paraphrase & intent recall │
    └──────────────┬────────────────┘                               └──────────────┬────────────────┘
                   │                                                               │
                   └───────────────────────────────┬───────────────────────────────┘
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │          4. FUSION & RERANK            │
                               │  • Reciprocal Rank Fusion (RRF)        │
                               │  • Optional Cross-Encoder Reranker     │
                               └────────────────────────────────────────┘
```

### Why Decoupling These Three Primitives Matters:

1. **Standalone Header Extractor (`extractor.py`):**
   * Can be used independently by linters, table-of-contents generators, or agent prompt-packers without dragging in SQLite or ONNX dependencies.
   * Produces uniform `(heading, start_line, end_line, content, sha256)` data structs.

2. **Zero-AI Fast Search Mode (`lexical.py`):**
   * On low-power devices (phones, low-spec laptops, battery-saver modes), the engine can run purely in **Lexical Fast Search** mode with **0% GPU usage, 0MB model RAM, and instantaneous startup**.

3. **Opt-in Neural Vectors (`vectors.py`):**
   * The vector engine acts as a pluggable enhancement layer. If ONNX/DirectML is available, it calculates embeddings; if unavailable or disabled, the entire search pipeline gracefully degrades to high-speed BM25.

---

## 📦 The 3 Distribution Packages

```
                               ┌────────────────────────────────────────┐
                               │        PACKAGE A: CORE ENGINE          │
                               │           pkm-search-core              │
                               │       (Python Library on PyPI)         │
                               └───────────────────┬────────────────────┘
                                                   │
                   ┌───────────────────────────────┴───────────────────────────────┐
                   ▼                                                               ▼
    ┌───────────────────────────────┐                               ┌───────────────────────────────┐
    │  PACKAGE B: OBSIDIAN PLUGIN   │                               │  PACKAGE C: SESSION SEARCHER  │
    │     obsidian-hybrid-search    │                               │      agent-session-search     │
    │    (Obsidian Community Store) │                               │      (Standalone CLI / TUI)   │
    └───────────────────────────────┘                               └───────────────────────────────┘
```

---

### Package A: Core Engine (`pkm-search-core` / `hypersearch`)

* **Target Audience:** Developers, agent builders, terminal power users.
* **Distribution:** PyPI package + standalone single-binary daemon release on GitHub.
* **Responsibilities:**
  - Pluggable Scanner API (`collect_data(root) -> tuple[notes, sections, edges, errors]`).
  - Section-level SHA256 caching & tail-read incremental indexing.
  - Background HTTP daemon (`127.0.0.1:44771`) with 0% idle CPU thread capping.
  - Model Context Protocol (MCP) server endpoint for Claude Code, Cursor, Antigravity, and Codex.
* **CLI Commands:**
  ```bash
  pkm-search daemon --watch /path/to/vault
  pkm-search query "boiler heating valve" --hybrid
  pkm-search mcp
  ```

---

### Package B: Obsidian Community Plugin (`obsidian-hybrid-search`)

* **Target Audience:** Obsidian PKM users seeking sub-5ms semantic search, instant backlinks, and vault intelligence without UI freezes.
* **Distribution:** Obsidian Community Plugins directory (following manifest and review guidelines).
* **Architecture:** Ultra-lightweight TypeScript frontend (<10ms load time) bridging Obsidian UI to `http://127.0.0.1:44771`.

#### 1. 🔗 Remade "Instant Backlinks & Smart Mentions" Leaf
* **The Problem with Native Backlinks:** Re-scans thousands of notes linearly in memory on active note changes, causing UI freezes and 12s+ startup delays (`collapse-backlinks` trace).
* **The Daemon Fix:** Single indexed query against the `edges` table in SQLite (`SELECT * FROM edges WHERE target = ?`) executing in **`< 0.2 ms`**.
* **Smart Unlinked Mentions:** SQLite FTS5 lookup that automatically excludes code blocks (`<pre><code>`) and frontmatter.
* **Semantic Neighbors ("Soft Backlinks"):** Surfaces top nearest-neighbor notes in embedding space—connecting notes that share concepts even if not explicitly linked.

```
┌─────────────────────────────────────────────────────────────┐
│                 INSTANT BACKLINKS LEAF                      │
│  [Active Note: "2026-08-29 Obsidian lazy loading"]         │
│                                                             │
│  ▼ Linked Backlinks (3) ────────────────────────── [0.1ms]  │
│    • [[2026-08-29 Startup Metrics Logger devlog]]:L15       │
│    • [[2026-08-29 local search daemon and indexer - release plan and modular decoupling]]:L8 │
│    • [[2026-08-29 agentic memory - scoped devlogs vs monolithic memory]]:L7 │
│                                                             │
│  ▼ Smart Unlinked Mentions (2) ─────────────────── [0.4ms]  │
│    • [[Obsidian faster startup]]:L26                        │
│      "...Move to delay startup group in Plugin Groups..."   │
│                                                             │
│  ▼ Graph Distance / Semantic Neighbours (3) ─────── [1.2ms] │
│    • [[2026-08-18 what retrieval costs as a vault grows]]   │
│    • [[token efficient PKM analysis architecture]]          │
└─────────────────────────────────────────────────────────────┘
```

#### 2. 🔍 Remade "Unified Hybrid Search & Quick Switcher"
* **Replaces Core Search & Quick Switcher:** Replaces native search sidebar and quick switcher with a unified search interface that talks to `127.0.0.1:44771/search`.
* **Search Modes via Prefixes:**
  * `Default`: Hybrid RRF combining BM25 keyword matching and neural vector similarity.
  * `? <query>`: Pure semantic meaning search (finds concepts without requiring shared words).
  * `"..."`: Instant SQLite FTS5 exact phrase search.
  * `#tag`: Instant tag explorer.
  * `@heading`: Subheading jumper.
* **Native Plugin Disabling:** Users can disable native core `Search` and `Backlinks` in Obsidian settings, immediately reclaiming CPU cycles and battery life.

---

### Package C: Agent Session Searcher (`agent-session-search`)

* **Target Audience:** Software engineers using coding agents (Claude Code, Gemini/Antigravity, Codex).
* **Distribution:** Standalone CLI tool (`pip install agent-session-search` / `brew install agent-session-search`).
* **Responsibilities:**
  - Scans agent transcripts across `~/.claude/projects/`, `~/.gemini/antigravity-cli/brain/`, and `~/.codex/sessions/`.
  - Incremental tail-reads over multi-gigabyte JSONL turn streams.
  - Interactive Terminal UI (TUI) with fuzzy search, syntax highlighting, and diff previews.
  - File provenance lookup: *"Which past session edited `main.ts`?"*

---

## 🗺️ Phased Rollout Roadmap

```
Phase 1: Core Modularization ──► Phase 2: Session CLI ──► Phase 3: Obsidian Plugin ──► Phase 4: Community Launch
 (Extract 3 primitives)           (Package agent search)    (Search + Backlinks UI)      (PyPI & Obsidian Store)
```

### Phase 1: Core Engine Refactoring & Primitives Isolation
- [ ] Separate `extractor.py` (header parser), `fts.py` (SQLite lexical), and `vectors.py` (ONNX).
- [ ] Expose clean pipeline API: `Engine.index()`, `Engine.search_lexical()`, `Engine.search_semantic()`, `Engine.search_hybrid()`.
- [ ] Ensure `--no-vectors` flag runs completely independent of ONNX / NumPy memory footprints.

### Phase 2: Standalone Session Searcher Release
- [ ] Package multi-agent transcript parsers (Claude, Antigravity, Codex).
- [ ] Build interactive Rich/Textual TUI for terminal browsing.
- [ ] Publish `agent-session-search` to PyPI and GitHub.

### Phase 3: Obsidian Frontend Bridge & UI Remake
- [ ] Initialize TypeScript repository `obsidian-hybrid-search` using the standard Community Plugin template.
- [ ] Implement **Unified Search & Quick Switcher** modal with prefix routing.
- [ ] Implement **Instant Backlinks & Smart Mentions** custom sidebar leaf.
- [ ] Implement daemon connectivity indicator in the status bar (🟢 *Connected* / 🔴 *Offline*).
- [ ] Validate against Obsidian Manifest guidelines and prepare automated GitHub release workflows.

### Phase 4: Public Distribution & Ecosystem Documentation
- [ ] Submit `obsidian-hybrid-search` to `community.obsidian.md`.
- [ ] Publish documentation benchmarks comparing search latency against native Obsidian search.
- [ ] Record development retrospective in project devlogs.

---

## 🔗 Related Notes
- [[progress - local-first search daemon and indexer]]
- [[cross-agent session indexing architecture]]
- [[core Obsidian features to rework on the vault index]]
- [[2026-08-27 tail reads, resuming an index at the byte it stopped at]]
- [[2026-08-18 what retrieval costs as a vault grows]]
- [[2026-08-29 agentic memory - scoped devlogs vs monolithic memory]]
- [[2026-08-29 Obsidian community plugin submission process]]
- [[multi-repo agentic search architecture]]
