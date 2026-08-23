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
│ (Exact commands & files)│ │ (Semantic intent matching)  │
└────────────┬────────────┘ └────────────┬───────────────┘
             └─────────────┬─────────────┘
                           ▼
              Reciprocal Rank Fusion (RRF)
                           ▼
              Hybrid Session Recall (<50ms)
```

## Schema Normalization Across Agents

Each tool formats turns differently, but all boil down to standard agent primitives:

- **`sessions` table:** `session_id`, `parent_session_id` (nullable FK → `sessions`, for subagent trees), `agent_type` (`antigravity` | `codex` | `claude`), `project_path`, `started_at`, `total_tokens`, `cost_estimate` (nullable — not all agents expose cost).
- **`turns` table:** `turn_id`, `session_id`, `turn_index`, `status` (`success` | `error` | `partial`), `user_prompt`, `assistant_response`, `thinking` (nullable), `tools_called` (JSON array), `files_touched` (JSON array), `token_count`.
- **`token_breakdown` table:** `turn_id`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens` — raw counts for recomputing cost when pricing changes.
- **`vectors` table:** `turn_id`, `embedding_model`, `chunk_sha256`, `vector` (384-dim float32 blob).
- **`file_edges` table:** `session_id`, `turn_id`, `file_path`, `action` (`view` | `search` | `edit` | `create` | `delete` | `execute`), `tool_name` (raw tool identifier for fine-grained filtering).

## Chunking & Caching Strategy

Instead of vault heading chunking (`^## `), session indexing chunks by **turn intent**:

**Primary chunk: User Prompt + Assistant Plan** (~150–300 tokens). For multi-tool turns where a single response contains 5+ tool calls with intermediate reasoning, chunk each (tool_call + tool_result) pair as a separate searchable unit. Apply the same 30-token minimum floor from [[pkm metadata indexer]] — trivial turns like "yes" or "continue" skip embedding to avoid vector noise.

**Incremental indexing:** Treat session JSONL as an append-only log. Track `file_mtime` + byte offset per file to index new turns without waiting for session completion (Antigravity sessions have no explicit end marker). SHA256 content hashing skips already-indexed turn blocks. Hash check: <50ms. Embedding new turns: ~1–5s depending on volume (GPU/DirectML).

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

## Open Concerns

**Security:** Agent transcripts routinely contain API keys, access tokens, and private code. A centralized `~/.agent_index.db` is a high-value target. Minimum: restrict file permissions to owner-only. Consider sensitive content filtering during ingest, encryption at rest if exposed over network.

**Storage scaling:** The [[pkm metadata indexer]] is ~114 MB for 6,599 notes with 17,567 chunks. Session indexing accumulates faster — a heavy user generating 50–100 sessions/week across three agents could reach 100k+ turns within months. Per [[agentic tooling upgrades over grep]] scaling milestones: FP16 matrix compression at >100k chunks, FAISS/sqlite-vec ANN at >500k if matmul exceeds 15ms.

**MCP integration:** Natural extension is exposing the index as an MCP server (`mcp-session-search`) so agents can query past sessions mid-conversation, similar to the MCP primitives in [[multi-repo agentic search architecture]].

**Implementation phasing:** Start with Antigravity (most structured JSONL, clearest step types). Add Claude Code second (requires dedup handling). Codex last (multiple SQLite DBs + event stream joins).
