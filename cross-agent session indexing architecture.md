---
tags:
  - ai
  - tools
  - architecture
  - search
  - multi-agent
---
Applying the hybrid search, vector embeddings, and SQLite indexing optimizations from [[pkm metadata indexer]] to unified session logs across Antigravity, Codex, and Claude Code.

## Problem: The Multi-Gigabyte Transcript Grep Bottleneck

Developers and autonomous workflows run multiple agent CLIs across projects:
- [[how to inspect antigravity cli sessions|Antigravity CLI]] stores structured steps in `~/.gemini/antigravity-cli/brain/`
- [[how to inspect Codex sessions|Codex CLI]] records turn streams in `~/.codex/sessions/`
- [[how to inspect Claude Code sessions|Claude Code]] logs project transcripts in `~/.claude/projects/`

When an agent needs past context (e.g. *"how did we resolve the Unity build failure last week?"* or finding earlier architecture trade-offs), naive `grep` must parse gigabytes of unindexed JSON Lines across disparate directory trees. As documented in [[agentic tooling upgrades over grep]], linear text scans burn tool latency and fail on fuzzy semantic concepts.

## Core Proposal: Unified Agent Session Indexer

Adapt the three-tier retrieval engine from [[vault hybrid search]] to index agent execution histories into a centralized SQLite database (`~/.agent_index.db`):

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
│ (Exact commands & files)│ │ (User intent & vibes)      │
└────────────┬────────────┘ └────────────┬───────────────┘
             └─────────────┬─────────────┘
                           ▼
              Reciprocal Rank Fusion (RRF)
                           ▼
           Sub-millisecond Session Recall (<5ms)
```

## 1. Schema Normalization Across Agents

Each tool formats turns differently, but all boil down to standard agent primitives:

- **`sessions` table:** `session_id`, `agent_type` (`antigravity` | `codex` | `claude`), `project_path`, `started_at`, `total_tokens`, `cost_estimate`.
- **`turns` table:** `turn_id`, `session_id`, `turn_index`, `user_prompt`, `assistant_response`, `tools_called` (JSON array), `files_touched` (JSON array), `token_count`.
- **`vectors` table:** `turn_id`, `embedding_model`, `chunk_sha256`, `vector` (384-dim float32 blob).
- **`file_edges` table:** `session_id`, `turn_id`, `file_path`, `action` (`read` | `write` | `execute`).

## 2. Chunking & Caching Strategy

Instead of vault heading chunking (`^## `), session indexing chunks by **turn intent**:
1. **User Prompt + Assistant Plan:** Embed as the primary semantic search target (~150–300 tokens).
2. **SHA256 Content Deduplication:** Sessions are immutable once finished. An incremental hash check skips already-indexed turn blocks, indexing new sessions in <50ms.
3. **Tool Call & File Inversion:** Index tool arguments and changed files directly into SQLite inverted indexes for instant lookup (e.g. `WHERE files_touched LIKE '%index_pkm_meta.py%'`).

## 3. High-Value Retrieval Capabilities

- **Cross-Agent Concept Search:** Search *"DirectML embedding benchmark"* and instantly receive the exact Claude Code turn, Antigravity task ID, or Codex rollout that ran the benchmark.
- **File Provenance & Blame Traversal:** Query any file path to retrieve every session turn from every agent that ever edited or debugged it.
- **Failure Recovery:** Filter turns by `error` status to find past workarounds for identical compiler or runtime exceptions across projects.

### Related
- [[agentic tooling upgrades over grep]]
- [[pkm metadata indexer]]
- [[vault hybrid search]]
- [[multi-repo agentic search architecture]]
- [[how to inspect antigravity cli sessions]]
- [[how to inspect Codex sessions]]
- [[how to inspect Claude Code sessions]]
