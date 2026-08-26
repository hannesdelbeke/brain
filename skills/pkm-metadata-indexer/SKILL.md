---
name: pkm-metadata-indexer
description: Fast local metadata, neural section embeddings, link graph, and hybrid search for Markdown notes in SQLite.
aliases:
  - pkm metadata indexer
  - pkm-metadata-indexer
origin-sha: "062084521"
created: 2026-08-20
tags:
  - technical
  - pkm
  - skill
---

Fast local metadata, neural section embedding, link graph, and hybrid search tool for Markdown notes. 

Parses frontmatter, heading-level sections (`^## `), wikilinks, and vector embeddings (`bge-small-en-v1.5`) directly into a local SQLite database (`.obsidian/pkm_index.db`).

## Commands & Usage

### 1. Build / Update Index
Scans the vault, caches frontmatter, extracts wikilink edges, and embeds new or modified sections:
```bash
python skills/pkm-metadata-indexer/index_pkm_meta.py
# Fast build skipping neural embeddings (metadata + links only):
python skills/pkm-metadata-indexer/index_pkm_meta.py --skip-embeddings
```

### 2. Fast Semantic Search Tool
A thin client over the daemon below, falling back to an in-process search when no daemon answers:
```bash
python skills/pkm-metadata-indexer/search_vault.py "notes on feeling overwhelmed by projects"
python skills/pkm-metadata-indexer/search_vault.py "battery mode" --vault work --top 5
python skills/pkm-metadata-indexer/search_vault.py "battery mode" --direct
```
Both paths call the same `search_index`, so results do not depend on whether the daemon happened to be up. A daemon hit takes 0.6s end to end, almost all of it Python starting; `--direct` takes about 2s because it loads the model.

### 3. In-Indexer Hybrid Search
Searches vault sections using combined lexical matching and neural vector cosine similarity (via in-memory GPU/CPU matrix multiplication):
```bash
python skills/pkm-metadata-indexer/index_pkm_meta.py --search "notes on feeling overwhelmed by projects"
```

### 3. Duplicate Note Prevention
Checks for semantic overlap before creating a new note to prevent note sprawl:
```bash
python skills/pkm-metadata-indexer/index_pkm_meta.py --check-duplicate "Obsidian link graph complexity"
```

### 4. Link Graph Queries
Instant lookup of inbound backlinks and outbound connections:
```bash
python skills/pkm-metadata-indexer/index_pkm_meta.py --links "Obsidian"
```

### 5. Index Stats & Performance Profiling
View database size, note count, indexed sections, graph edge counts, and run execution performance history:
```bash
python skills/pkm-metadata-indexer/index_pkm_meta.py --stats
# Or view performance benchmarks directly:
python skills/pkm-metadata-indexer/index_pkm_meta.py --perf
```

### 6. Resident Search Daemon (`searchd.py`)
Every CLI call above pays about 3.0s to load the embedding model before it can encode a single query. The daemon loads it once and serves the same `search_index` over HTTP on `127.0.0.1:44771`, which takes a query to 13-22ms. One process serves every vault, because the model is the expensive part and it is vault-independent:
```bash
python skills/pkm-metadata-indexer/searchd.py --vault brain=/path/to/brain --vault work=/path/to/work
python skills/pkm-metadata-indexer/searchd.py --vault brain=/path/to/brain --sessions claude=~/.claude/projects
curl "http://127.0.0.1:44771/search?q=battery+mode&vault=work&limit=5"
curl http://127.0.0.1:44771/links?note=Obsidian
curl -X POST "http://127.0.0.1:44771/reindex?vault=brain"
curl http://127.0.0.1:44771/health
```
By default, the daemon idles near zero CPU and answers warm queries in 10-35ms. Running a periodic keepalive loop is discouraged on multi-core systems because ONNX Runtime's intra-op thread pool defaults to busy-spinning (`allow_spinning = 1`), which burns full CPU cores continuously between pings. Keeping the thread pool parked at idle maintains sub-35ms response times with zero background CPU overhead.

Every consumer speaks the same HTTP contract, so an agent, an editor plugin, a launcher and a shell alias all share one index and one model. Requests carrying an `Origin` header are refused and the `Host` must be loopback, which keeps a web page in the browser from reading the vault. To reach it from another machine, pass `--bind 0.0.0.0 --token <secret>` and send `X-PKM-Token`; a non-loopback bind without a token is refused rather than silently publishing the vault.

Tests: `python -m unittest test_searchd test_index_pkm_meta test_index_sessions`.

### 7. Open Problem Finder (`find_open_problems.py`)
Ranks notes by how likely they still describe an unsolved problem, so an agent can pick work without reading the vault:
```bash
python skills/pkm-metadata-indexer/find_open_problems.py --top 30
python skills/pkm-metadata-indexer/find_open_problems.py --min-score 5
python skills/pkm-metadata-indexer/find_open_problems.py --self-test
```
It scans markdown directly rather than the index, so a stale or missing database does not matter; a full pass over 3200 notes takes about 2s. Score comes from a problem-shaped heading with no solution-shaped heading (+3), a `TODO ` title prefix (+3), open task checkboxes (+1 each, capped at 3), and body markers such as "unresolved", "doesn't work" or "can't figure out" (+2). Notes carrying the `solved` tag score zero and drop off the list permanently, which is how a finished problem gets retired. See [[finding unsolved problems in my vault]].

### 8. Urgent Task Ranking (`urgent_tasks.py`)
Orders open `- [ ]` tasks by a time-based urgency score, for tasks whose importance changes with the calendar rather than with their wording:
```bash
python skills/pkm-metadata-indexer/urgent_tasks.py
python skills/pkm-metadata-indexer/urgent_tasks.py --top 40 --min-score 0
python skills/pkm-metadata-indexer/urgent_tasks.py --selfcheck
```
Score is `100 / max(3, days_until_due + 3) + days_since_created / 3`, so a deadline term that stays near zero until the last weeks then climbs to 33 on the due date, plus a rot term of one point per three days a task has sat. Dates come from `[due:: YYYY-MM-DD]` and `[created:: YYYY-MM-DD]` inline fields or the equivalent 📅 and ➕ emoji. Like the open problem finder it reads markdown directly, ignores fenced code blocks so documented examples do not rank, and skips tasks with neither date. See [[TODO how to highlight urgent tasks]].

### 9. Mention Heatmap (`mention_heatmap.py`)
Ranks wikilink targets by how often they were newly written over time, so a subject that keeps coming back surfaces above one that is merely linked from many old notes:
```bash
python skills/pkm-metadata-indexer/mention_heatmap.py
python skills/pkm-metadata-indexer/mention_heatmap.py --days 30 --top 40
python skills/pkm-metadata-indexer/mention_heatmap.py --selfcheck
```
Score is `sum over distinct days a target was mentioned of 0.5 ** (age_days / 30)`, so a mention written today is worth 1 and one written 30 days ago is worth 0.5. Each day counts once however many times the link appears that day. It reads `git log -p` rather than the `edges` table, because `edges` holds the current graph with no dates, and in-degree over the whole vault ranks hubs such as Obsidian and Python instead of live work. A 180 day window costs about 1.7s. Output is a sorted list with a block bar. See [[Priority heatmap]].

### 10. Unlinked Mentions (`GET /unlinked`)
Sections that name a note without linking to it, served from the index instead of Obsidian's own pane:
```bash
curl "http://127.0.0.1:44771/unlinked?note=Zettelkasten&limit=20"
python skills/pkm-metadata-indexer/search_vault.py "Zettelkasten" --unlinked
python skills/pkm-metadata-indexer/search_vault.py "Zettelkasten" --unlinked --direct
```
Matching is an FTS5 phrase over `sections_fts`, so it is token-based: `covariance` does not match `covariances`, which the pane's substring match does. Frontmatter `aliases` count as titles and are read from the target file at query time, one file read per query, because the index does not store them. Five things are excluded: the note itself; sections already holding a `[[wikilink]]` to it under any alias; matches inside a fenced code block (the complaint in [[Obsidian unlinked mentions include code snippets]], using the same fence toggle as `urgent_tasks.py`); matches inside a code span, for the same reason; and matches sitting inside a link to some other note. Results are ordered by bm25 and carry path, heading, line number and a snippet with the term in brackets. The endpoint and the CLI call one `find_unlinked_mentions`, so they cannot drift.

Measured over 3,228 notes and 6,550 sections at `limit=20`: a narrow title (`Zettelkasten`, 7 hits) costs 20ms in the daemon and 34ms over HTTP; a hub title (`Obsidian`, `Python`, both capped at 20 hits) costs 41-48ms and 57-59ms, because bm25 ranks every section holding the word before the top 200 is taken. A first call against a freshly started daemon costs the same, since this endpoint keeps no resident state, unlike `/search` and its model. Through the CLI a call is 0.38s against the daemon and 1.53s with `--direct`, both Python startup. Limits: one hit per section, the first; a mention inside a URL or a markdown link label still counts; an unclosed fence marks the rest of the file as code. No plugin calls this yet. See [[unlinked mentions from the vault index]].

### 11. Nearest Notes (`GET /similar`)
Notes closest to one note, ranked by cosine against the vectors already in the index:
```bash
curl "http://127.0.0.1:44771/similar?note=Obsidian%20graph%20view&limit=12&vault=brain"
```
`/search` spends about 220ms encoding the query string on `CPUExecutionProvider`, which is most of the cost of a call and is pure waste when the note is already indexed. `find_similar_notes` mean-pools the note's own section vectors instead, normalises, and multiplies the resident matrix, so no model runs: 11-26ms over HTTP at `limit=36` on 3,228 notes and 6,550 sections, against 228-541ms for the same note through `/search`. The note itself is excluded and each other note appears once, at its best-matching section. Response shape matches `/search`, so a caller only changes the URL. An unresolvable or ambiguous note reference returns `{"error": ...}` rather than an empty list, which is how a caller tells "not indexed yet" apart from "no neighbours" and decides whether to fall back to `/search`. That fallback is what the Semantic Local Graph plugin does for a note written since the last reindex. See [[core Obsidian features to rework on the vault index]].

### 12. Agent Session Index (`index_sessions.py`)
Indexes agent transcripts into the same tables as notes, so past sessions are searchable by the same query path:
```bash
python skills/pkm-metadata-indexer/index_sessions.py --root ~/.claude/projects
python skills/pkm-metadata-indexer/index_sessions.py --root ~/.claude/projects --with-embeddings
python skills/pkm-metadata-indexer/searchd.py --sessions claude=~/.claude/projects
```
A transcript is a note, a turn is a section, and a subagent spawn is an edge back to the session that spawned it, so `search_index`, `query_links` and the SHA256 cache work unchanged. Every file a tool touched is also an edge, which answers "which session last edited this file" from the graph rather than from git. `build_index` takes a `collect=` scanner for this, and the markdown scanner is still the default, so there is one index format and two front ends rather than two systems.

Only prose and a whitelist of tool arguments are indexed. Tool results are about 80% of the corpus by size, they hold whatever secrets and file dumps passed through the session, and the files they read are still on disk; thinking blocks are another 6% and are skipped for now. Client-generated user turns (slash commands, hook output, `isMeta` caveats, task notifications) are dropped before they can become the session title, and text under 30 characters never gets a vector.

Measured over 766 transcripts and 1.49 GB: a metadata-only pass takes 2m05s (102s parsing JSON Lines, 21s committing) and produces 70,418 sections and 8,524 edges in a 101 MB database at `~/.claude/projects/.pkm_index.db`. Lexical-only queries over that run 30-58ms, against 13-22ms for the hybrid vault index at a tenth the sections. Embeddings are a later flag rather than a prerequisite, because `search_index` degrades to lexical when a corpus has no vectors. Chunk headings carry the session's first real prompt, which labels a turn by its session rather than by itself. See [[cross-agent session indexing architecture]].

## What it extracts
- **Frontmatter metadata:** energy, sentiment, sentiment_labels, tags.
- **Heading-Level Sections:** Sections split by `## ` with line numbers and SHA256 hashes for incremental caching.
- **Neural Embeddings:** 384-dimensional dense vectors (`BAAI/bge-small-en-v1.5`) stored as float32 blobs.
- **Link Graph (`edges`):** All source-to-target `[[wikilinks]]` for instant traversal without grepping files.

## Why use this
Enables instant SQL aggregations and single-turn semantic search across thousands of notes with zero ongoing API costs, serving as an intelligent pre-filter for agents.

### Related
- [[agentic tooling upgrades over grep]]
- [[vault hybrid search]]
- [[offline GPU embeddings with incremental cache]]
- [[vault graph traversal]]
- [[token efficient PKM analysis architecture]]
