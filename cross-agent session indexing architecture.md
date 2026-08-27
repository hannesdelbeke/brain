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

**Status, 2026-08-27: built for Claude Code.** `index_sessions.py` is the adapter, 859 transcripts and 1.49 GB index to 79,489 sections and 9,738 edges, and `searchd.py --sessions claude=~/.claude/projects` serves them beside the vault. Queries run 34-62ms with vectors and 30-58ms without. A first pass costs 19.24s of metadata plus 298.86s of embedding; after it, a transcript only grows, so a reindex parses the appended bytes and finishes in 7.78s ([[2026-08-27 tail reads, resuming an index at the byte it stopped at]]). What follows is the design and what measurement changed about it; Antigravity and Codex are still unwritten.

The engine needed no new index, ranker or daemon. `build_index` gained one `collect=` parameter naming the scanner, the markdown scanner stayed the default, and everything after the scan was already source-agnostic.

## Problem: The Multi-Gigabyte Transcript Grep Bottleneck

Developers and autonomous workflows run multiple agent CLIs across projects:
- [[how to inspect antigravity cli sessions|Antigravity CLI]] stores structured steps in `~/.gemini/antigravity-cli/brain/`
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

**Security:** Agent transcripts routinely contain API keys, access tokens, and private code, so a single index over all of them is a high-value target. Dropping `tool_result` bodies for size reasons removes most of that exposure as a side effect, since the env dumps and file contents live there rather than in prose. What remains: keep the database beside the transcripts rather than inside any repository, because the transcripts already carry whatever the repositories separate, and owner-only permissions. Serving it over the network needs the daemon's token, never a bare bind.

**Storage scaling:** The [[pkm metadata indexer]] is ~114 MB for 6,599 notes with 17,567 chunks, and the measured session corpus is ~30k chunks once tool output is dropped, so this sits inside the range the current matmul already handles at 0.4ms. Per [[agentic tooling upgrades over grep]] scaling milestones the next moves are FP16 compression at >100k chunks and sqlite-vec or HNSW at >500k, neither of which is close.

**Agent integration:** answered by the daemon, so this is no longer a fork in the road. The index is a registered corpus on `127.0.0.1:44771` and any consumer can query it over HTTP with the model already resident, which is what made the skill-versus-MCP tradeoff a tradeoff. A skill is still the cheap surface for an agent that prefers a command, and MCP becomes a thin wrapper worth adding when an agent needs a native tool rather than a shell call. Neither owns the engine.

**Implementation phasing:** Claude Code first, not Antigravity as originally planned. Its transcripts are the largest corpus by far, its dedupe trap is already solved by the parsers written for cost auditing, and reusing them is the step that pays for itself whether or not the indexing lands. Antigravity second, Codex last (multiple SQLite databases plus event stream joins).

1. **Extract the transcript reader.** `iter_events(path)` yields deduplicated events, keyed on `(message.id, text)` because the client writes a line per content block and reuses the id. It streams, which matters when the largest transcript here is 79 MB.
2. **Write the scanner against the seam.** `scan_sessions(root)` matches `collect_index_data`'s contract, and `build_index(collect=...)` takes it.
3. **Register it:** `searchd.py --sessions claude=<root>`, a separate flag rather than a `--vault` prefix so the scanner choice is explicit. `default_db_path` falls back to `<root>/.pkm_index.db` when the root has no `.obsidian`, which also deduplicated the six copies of that path expression in the indexer.

First slice is FTS5-only. `search_index` already degrades to lexical when a corpus has no vectors, so embedding is a later flag rather than a prerequisite.

What step 1 did not buy: the cost-audit parsers still re-implement their own loop. They need `message.usage`, which `iter_events` deliberately drops, so sharing the reader would mean widening it back out to the thing it exists to avoid. Indexing for recall and accounting for spend read the same files and want different halves of them.

Left for later: no watcher, so the index is as fresh as the last `--reindex`, and an append-only log deserves a byte-offset resume rather than the full 102-second reparse. Embeddings are a flag nobody has turned on yet.
