---
aliases:
  - semantic search on pkm session data
  - cross-agent session indexing architecture
  - session indexing architecture
tags:
  - ai
  - tools
  - architecture
  - search
  - multi-agent
---
Applying the hybrid search, vector embeddings, and SQLite indexing optimizations from [[pkm metadata indexer]] to unified session logs across Antigravity, Codex, and Claude Code.

**Status, 2026-08-30: built for Claude Code and Antigravity.** `index_sessions.py` is the adapter, 859 transcripts and 1.49 GB index to 79,489 sections and 9,738 edges, and `searchd.py --sessions claude=~/.claude/projects` serves them beside the vault. Queries run 34-62ms with vectors and 30-58ms without. A first pass costs 19.24s of metadata plus 298.86s of embedding; after it, a transcript only grows, so a reindex parses the appended bytes and finishes in 7.78s ([[2026-08-27 tail reads, resuming an index at the byte it stopped at]]). Antigravity followed on 2026-08-30 as `index_agy.py`, and Codex is still unwritten. What follows is the design and what measurement changed about it.

The engine needed no new index, ranker or daemon. `build_index` gained one `collect=` parameter naming the scanner, the markdown scanner stayed the default, and everything after the scan was already source-agnostic.

## Problem: The Multi-Gigabyte Transcript Grep Bottleneck

Developers and autonomous workflows run multiple agent CLIs across projects:
- [[how to inspect antigravity cli sessions|Antigravity CLI]] stores structured steps in one SQLite database per conversation under `~/.gemini/antigravity-cli/conversations/`, as binary protobuf with no published schema
- [[how to inspect Codex sessions|Codex CLI]] records turn streams in `~/.codex/sessions/`
- [[how to inspect Claude Code sessions|Claude Code]] logs project transcripts in `~/.claude/projects/`

When an agent needs past context (e.g. *"how did we resolve the Unity build failure last week?"* or finding earlier architecture trade-offs), naive `grep` must parse gigabytes of unindexed JSON Lines across disparate directory trees. As documented in [[agentic tooling upgrades over grep]], linear text scans burn tool latency and fail on fuzzy semantic concepts.

## Core Proposal: Unified Agent Session Indexer

Point the existing engine from [[vault hybrid search]] at agent execution histories, writing to a database beside the transcripts rather than inside any repository:

```
┌────────────────────────────────────────────────────────┐
│             Cross-Agent Session Sources                │
│  Antigravity (.gemini)  |  Codex (.codex)  |  Claude   │
└──────────────────────────┬─────────────────────────────┘
                           │ Parse & Hash
                           ▼
┌────────────────────────────────────────────────────────┐
│             Unified Turn Normalizer                    │
│   (turn_id, agent_type, prompt, plan, tools, diffs)    │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
┌─────────────────────────┐ ┌────────────────────────────┐
│ SQLite FTS5 + Metadata  │ │ GPU / DirectML Vectors     │
│ (Exact commands & files)│ │ (Semantic intent matching)  │
└────────────┬────────────┘ └────────────┬───────────────┘
             └─────────────┬─────────────┘
                           ▼
              Reciprocal Rank Fusion (RRF)
                           ▼
              Hybrid Session Recall (<50ms)
```

## Schema Normalization Across Agents

Each tool formats turns differently, but all boil down to standard agent primitives, and those primitives are the ones the vault indexer already stores. A session is a document, a turn is a section, and a subagent spawn is a link, so the existing `notes` / `sections` / `edges` tables take sessions with no schema of their own:

| Session concept | Existing column | Note |
| :--- | :--- | :--- |
| session file | `notes.path`, `notes.mtime` | the transcript path is the document identity |
| `agent_type`, `project_path`, `started_at` | `notes` frontmatter columns | already a generic metadata bag |
| turn | `sections` row with `heading` and `start_line` | line number points at the jsonl line, so a result opens where it happened |
| turn text | `sections_fts` + `sections.vector` | same BM25, same 384-dim blob, same RRF |
| unchanged turn | `sections.content_sha256` | the incremental cache works unmodified on an append-only log |
| `parent_session_id`, files touched | `edges` | subagent trees and file provenance are both edges, so `query_links` answers both |

The one thing the vault schema does not carry is the token counts, which is fine: cost auditing already parses the same files for `message.usage` and is a different job with a different output. Indexing for recall and accounting for spend should not share a table just because they share a source.

**The reuse seam, as built.** The split the note asked for was already there: `collect_index_data(root)` returns `(notes, sections, links, errors)` and nothing downstream cares where those came from. So the change was `build_index(..., collect=None)` defaulting to the markdown scanner, and `scan_sessions(root)` returning the same four lists. No document dataclass, no `index_documents`, no code moved. A transcript adapter is a generator, not a subsystem, and the seam it needed was one parameter.

Two things fell out of reusing the note schema rather than designing a session schema. `notes.filename` feeds `note_titles_fts`, so putting the session's first real prompt there makes a session findable by what it was about; the same string becomes the chunk heading, which carries the session subject into turns that never restate it, at the cost of labelling every turn by its session rather than by itself. And `edges` took file provenance for free: every `file_path` a tool touched is an edge from the session, so "which session last edited this file" is a graph query rather than a git archaeology session.

## Chunking & Caching Strategy

**Measure the corpus before sizing anything.** 751 Claude Code transcripts on this machine, 1.49 GB, sampled 25 files and totalled every content block by type:

| Block | Share |
| :--- | :--- |
| `tool_result` | 80.8% |
| attachments | 6.5% |
| `thinking` | 6.0% |
| `tool_use` | 4.3% |
| user prose | 1.2% |
| assistant prose | 1.0% |

Four fifths of the corpus is tool output: file dumps, command output, search results. It is the least worth embedding, because the file it came from is still on disk and searchable in place, and it is where the API keys and private code are. Indexing prose and `tool_use` arguments only takes 1.49 GB to about 95 MB, which is one embedding pass of a few minutes at the measured 165 vec/sec rather than the multi-hour job the raw size implies. The 100k+ chunk scaling worry below is what the raw number causes and the composition removes.

The chunk estimate was low. 70,418 sections, not 30k, because a `tool_use` is a section of its own and a working session is mostly tool calls. That is still inside the range the current matmul handles, and it is 7 minutes of embedding rather than 3.

One filter had to be added that the composition table does not show. The client writes its own slash commands, hook output, `isMeta` caveats and task notifications into the transcript as user turns, and they are formulaic enough to dominate both titles and BM25. Dropping any user text opening with one of those tags, plus anything under 30 characters, is what separates a session titled `make the widget stop crashing` from one titled `<command-name>/clear</command-name>`.

Instead of vault heading chunking (`^## `), session indexing chunks by **turn intent**:

**Primary chunk: User Prompt + Assistant Plan** (~150–300 tokens). For multi-tool turns where a single response contains 5+ tool calls with intermediate reasoning, chunk each (tool_call + tool_result) pair as a separate searchable unit. Apply the same 30-token minimum floor from [[pkm metadata indexer]] — trivial turns like "yes" or "continue" skip embedding to avoid vector noise.

**Incremental indexing:** Resume rather than reparse, by whatever unit the store appends in. Claude Code appends JSON Lines, so the resume point is a `file_mtime` plus a byte offset per file. Antigravity appends rows, so the resume point is the highest `steps.idx` read, and the last step is reread because Antigravity rewrites it in place while the answer streams. Neither waits for session completion, since neither format has an explicit end marker. SHA256 content hashing skips already-indexed turn blocks. Hash check: <50ms. Embedding new turns: ~1–5s depending on volume (GPU/DirectML).

**Tool call & file inversion:** Index tool arguments and changed files via the `file_edges` table and FTS5 for instant structured lookup:
```sql
SELECT * FROM turns
JOIN file_edges USING(turn_id)
WHERE file_path = 'index_pkm_meta.py'
```

**Parser caveats:** Claude Code streams multiple JSONL lines per message block and repeats `message.id`. The ingest pipeline must deduplicate on `(message.id, text)` to avoid duplicate turns — see [[how to inspect Claude Code sessions]] for details.

## High-Value Retrieval Capabilities

Apply top-500 candidate pre-filtering before RRF to avoid O(N log N) sorting bottlenecks as turn volume grows, consistent with [[agentic tooling upgrades over grep]] scaling rules. Expected corpus: 50k–500k turns after a year of heavy use across three agents.

- **Cross-Agent Concept Search:** Search *"DirectML embedding benchmark"* and instantly receive the exact [[Claude Code]] turn, [[antigravity]] task ID, or Codex rollout that ran the benchmark.
- **File Provenance & Blame Traversal:** Query any file path to retrieve every session turn from every agent that ever edited or debugged it.
- **Failure Recovery:** Filter turns by `error` status to find past workarounds for identical compiler or runtime exceptions across projects.
- **Subagent Tree Traversal:** Follow `parent_session_id` chains to reconstruct what a research subagent discovered during a larger autonomous task.

## Shipped Milestones (as of 2026-08-28)

* [x] **Session Corpus Ingestion:** 859 transcripts (1.49 GB) parsed and indexed down to 79,489 sections and 9,738 subagent / file edges in SQLite (`.pkm_index.db`).
* [x] **Local Hybrid Search:** FTS5 BM25 + ONNX DirectML `bge-small-en-v1.5` embeddings fused via Reciprocal Rank Fusion (RRF). Queries execute in 34–62ms warm.
* [x] **Tail Reads on Transcripts:** Byte-offset resume parses only newly appended bytes, reducing incremental updates from 12.46s to 0.78s ([[public/2026-08-27 tail reads, resuming an index at the byte it stopped at|tail reads]]).
* [x] **Antigravity Adapter:** `index_agy.py` reads schema-free protobuf out of one SQLite database per conversation, resuming on `steps.idx` rather than a byte offset, and reaches the daemon through `--corpus` without adding code to it.
* [x] **Live File Watchers:** `searchd --watch` runs multi-corpus watchers using `watchfiles` with a 2-second debounce and indexer write filtering.
* [x] **Cross-Encoder Reranking & Privacy Gates:** Optional `ms-marco-MiniLM-L-6-v2` reranker with `--withhold-private` regex scanner ensuring zero telemetry egress for sensitive credentials, home paths, or network IPs.
* [x] **Graph & File Provenance Queries:** `link_graph.py` queries file references across sessions, identifying which agent session last modified or debugged any code or document asset.

---

## Prior Art & Industry Landscape

The problem of giving coding agents durable memory across sessions spans several established patterns:

### 1. File-Based Instructions (`CLAUDE.md`, `AGENTS.md`)
* The industry standard for lightweight context.
* **Limitations:** Prone to manual maintenance drift, context bloat, and probabilistic degradation as files grow.

### 2. Session Transcript Indexing & MCP Search Tools
* **[SessionFlow](https://github.com/lbruton/SessionFlow):** Indexes Claude Code transcripts locally on Apple Silicon (MLX) and serves them via Model Context Protocol (MCP).
* **[devmemory](https://github.com/shahriyar_r/devmemory):** Syncs Git commits and agent execution logs to a Redis-backed memory store so agents recall architectural decisions.
* **[ai-memory](https://github.com/AkitaOnRails/ai-memory):** Intercepts agent lifecycle events to auto-generate markdown summary wikis, avoiding raw log re-indexing bottlenecks.

### 3. Extraction-First Memory vs. Compositional Pruning
* Tools like **Mem0**, **prism-mem**, and **Cognee** extract entity-relation triples (Knowledge Graphs) from conversation logs before indexing.
* **Our Alternative (Compositional Pruning):** Rather than paying for continuous LLM extraction passes, we exploit transcript block composition: dropping `tool_result` bodies (which make up 80.8% of payload) reduces a 1.49 GB corpus to 95 MB of high-signal prompt/plan text, eliminating secret exposure and making local DirectML matrix multiplication faster (<1ms) than external graph queries.

### Comparison Matrix

| Feature | Cloud Memory (Mem0 / Letta) | Local MCP Tools (SessionFlow) | Our Session Indexer (`pkm-search`) |
| :--- | :--- | :--- | :--- |
| **Data Privacy** | Cloud API storage / egress | Local machine | **100% Local-First** (Zero egress, DirectML ONNX) |
| **Ingest Latency** | Async LLM extraction pipeline | Full file scan | **Resume per store** (byte offsets, 0.78s incremental; step cursors for Antigravity, 0.26s) |
| **Retrieval Strategy** | Vector-only or GraphRAG | Pure Vector Search | **Hybrid RRF** (FTS5 BM25 + Vectors + Reranker) |
| **Multi-Agent Normalization** | Single agent harness | Claude Code only | **Unified Schema** (Claude and Antigravity shipped, Codex unwritten) |
| **Live Sync & Invalidation** | Periodic re-sync | Static batch index | **`watchfiles` + split-lock resident daemon** |

---

## Open Tasks & Next Steps

1. **Codex Adapter:** Write the scanner for Codex (`~/.codex/sessions/`) to fulfill the multi-agent contract. Antigravity landed on 2026-08-30 as `index_agy.py`: 18 conversations and 44 MB down to 17 notes, 1,511 sections, 107 edges and 2.4 MB of index, served through `searchd.py --corpus` with no code of its own. Its field map was read out of the wire format by volume rather than from a schema, so `index_agy_validation.md` is the procedure for rechecking it on a larger corpus.
2. **Cross-Machine Sync Layer:** Transcripts remain local to each workstation; building a lightweight sync or Git-backed metadata exchange is required for multi-device recall.
3. **Supervisor Integration:** Feed session turns directly into [[public/proposal - self-learning agent supervisor and continuous prompt failure distillation|self-learning agent supervisor]] to automatically cluster human correction prompts.

---

Related:
- [[public/proposal - self-learning agent supervisor and continuous prompt failure distillation|proposal - self-learning agent supervisor and continuous prompt failure distillation]]
- [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]]
- [[public/2026-08-27 tail reads, resuming an index at the byte it stopped at|tail reads on transcript corpus]]
- [[public/vault hybrid search|vault hybrid search]]
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]

