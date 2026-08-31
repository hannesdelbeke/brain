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
# Target a specific named corpus:
python skills/pkm-metadata-indexer/index_pkm_meta.py --corpus brain
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
A keepalive thread encodes a throwaway string every 250ms so the model never goes cold, and it is on by default; `--no-keepalive` turns it off and trades about 30ms on the first query after idle. Keepalive used to be discouraged because ONNX Runtime's intra-op pool busy-spins between pings (`allow_spinning = 1`) and burned 11.93 of 12 cores; capping the query path at `QUERY_THREADS = 1` brings a warm idle daemon to 0.000 cores, so the reason to avoid it is gone. Warm queries answer in 10-35ms either way.

`&rerank=1` on `/search`, or `--rerank` on the CLI, reorders the fused top 20 with a cross-encoder that reads the query and each section together instead of comparing two vectors made apart. The model is `Xenova/ms-marco-MiniLM-L-6-v2` through the `fastembed` already installed, so it adds no dependency; the first call downloads about 90 MB and loads it lazily, and it is never loaded otherwise. It costs about 22ms per candidate, so 227ms over 10, 533ms over 20 and 706ms over 30, against a 26ms query, which is why it is opt-in. `RERANK_CANDIDATES` sets the depth. Results carry a `rerank_score` when it ran. On the query "how did we stop the laptop overheating" over 3,264 notes, fusion put the two sections that answer it at rank 9 and 11 and returned notes about laptop hardware and building ventilation above them; the rerank put both first with a score gap of 5.9 and 5.4 against -5.2 for the next.

`eval_rerank.py` is what says whether that generalises. It asks a question set of one corpus twice, once with the rerank and once without, and has a model judge each returned section from the section text alone, so the judge cannot see which run produced it or at what rank. Point it at a daemon serving the corpus: `python searchd.py --vault brain=<vault> --port 44781` then `python eval_rerank.py --vault brain --port 44781`, with `--self-check` for the scoring asserts. Judgements cache in `~/.pkm/rerank-judgements.json`. Over 13 hold-out questions on a 3,228-note vault, precision@10 was 39% with the rerank against 32% without, first useful section at mean rank 1.6 against 1.9, seven questions better, three worse, three unchanged.

`--withhold-private` keeps a section on the machine rather than sending it to a judge that runs elsewhere, on the patterns in `PRIVATE`: home paths, credentials, LAN addresses, contact details, house automation, health and money words. A withheld section counts as not useful in both runs, so the comparison stays fair and the absolute precision reads low, which is why the report carries a judged-only column and a count of what was held back. The same 13 questions over 859 agent transcripts, 79,645 sections, with 63 of 145 sections withheld: precision@10 28% with the rerank against 22% without, 46% against 34% over the sections a judge actually saw, first useful section at mean rank 2.9 against 3.9, and 11 of 13 questions answered against 10.

`--watch` starts one watcher thread per corpus and reindexes that corpus when its files change, so the index follows writes instead of being as fresh as the last manual reindex. It needs `watchfiles`. Changes are batched over a 2s debounce, so saving five files is one pass, and the indexer's own writes are filtered out — the database, its journals and every dotfile — because a reindex writing inside the watched root would otherwise trigger the next one. A pass that fails prints and the watcher keeps running, since a half-written file must not stop it. Cost is one pass per batch: 2.57s over 3,264 notes with nothing to re-embed, 0.02s over a handful. It also reindexes once at startup, before the socket opens, because a watcher only sees what changes while it runs and a daemon that was down over an edit would otherwise serve the index it was killed with. That catch-up is what makes starting the daemon on demand as good as leaving it running — 2.3s to answering plus one pass — so nothing needs to survive a reboot.
```bash
python skills/pkm-metadata-indexer/searchd.py --vault brain=/path/to/brain --watch
```

Every consumer speaks the same HTTP contract, so an agent, an editor plugin, a launcher and a shell alias all share one index and one model. Requests carrying an `Origin` header are refused and the `Host` must be loopback, which keeps a web page in the browser from reading the vault. To reach it from another machine, pass `--bind 0.0.0.0 --token <secret>` and send `X-PKM-Token`; a non-loopback bind without a token is refused rather than silently publishing the vault.

Every `/search` and `/similar` call appends one JSON Lines row to `~/.pkm/queries.jsonl`: timestamp, vault, query text, limit, latency and the result paths. It is a file rather than a table in the index because a reindex rebuilds the index, and a log a reindex deletes is not a log. Scores are left out, since they are reproducible from the query, while the paths are what a co-retrieval edge needs. A caller can say where a search came from with `&origin=<note>`, and `/similar` records the note as its own origin. `--query-log` moves the file and `--no-query-log` turns it off, which is the switch to reach for given it holds query strings in plain text.
```bash
tail -3 ~/.pkm/queries.jsonl
```

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

A reindex is a tail read. A transcript only ever grows, so each run records the byte it stopped at, the line number there and a hash of the 4 KB before it in `<root>/.pkm_scan_state.json`, and the next run seeks to that byte instead of parsing from the top. Rows for the untouched part come back out of the index itself, which already stores every section with its text, so nothing is cached twice. A file that shrank, whose prefix hash moved, or whose section count disagrees with the index is read in full, and any edit to `index_sessions.py` or to `CHUNKING_VERSION` changes a fingerprint in the state file that invalidates every offset — so a scanner change can never leave stale rows behind. Measured over 859 transcripts: parsing drops from 12.46s to 0.78s and the whole metadata-only pass from 19.24s to 7.78s, of which 6.6s is the FTS rebuild. A half-written last line has no newline yet, so it is left for the next run. `--full` reparses everything.

Only prose and a whitelist of tool arguments are indexed. Tool results are about 80% of the corpus by size, they hold whatever secrets and file dumps passed through the session, and the files they read are still on disk; thinking blocks are another 6% and are skipped for now. Client-generated user turns (slash commands, hook output, `isMeta` caveats, task notifications, the interrupt marker) are dropped before they can become the session title. A prose floor drops the rest of the noise, and it is asymmetric: 30 characters for an assistant turn, 10 for a user one. Over 120 transcripts, 15% of user prose sits under 30 characters and reads like "who is logged in gh", while the 6% of assistant prose that short is all "Now the tests." The floor drops the turn rather than only its vector, so a short first prompt would otherwise cost the session its title as well.

Measured at `~/.claude/projects/.pkm_index.db`: a metadata-only pass over 766 transcripts and 1.49 GB takes 2m05s (102s parsing JSON Lines, 21s committing) for 70,418 sections and 8,524 edges in 101 MB, and `--with-embeddings` over 858 transcripts adds 298.86s at 265.5 vec/s on DirectML for 79,359 vectors, 320.92s and 222 MB in total. Warm queries run 34-62ms with vectors and 30-58ms without, against 13-22ms for the vault index at a tenth the sections; the vector matrix is 122 MB resident in the daemon. Embeddings stay a flag rather than a prerequisite, because `search_index` degrades to lexical when a corpus has none. Chunk headings carry the session's first real prompt, which labels a turn by its session rather than by itself. See [[cross-agent session indexing architecture]].

### 13. Co-retrieval Edges (`co_retrieval.py`)
Notes that keep coming back in the same result set are related in a way their text does not say. The query log records the result paths of every `/search` and `/similar` call, so the association is derivable after the fact: read the log, add a point to every pair of notes that shared a result set, let old points fade.
```bash
python skills/pkm-metadata-indexer/co_retrieval.py
python skills/pkm-metadata-indexer/co_retrieval.py --vault brain --top 40
python skills/pkm-metadata-indexer/co_retrieval.py --rebuild
python skills/pkm-metadata-indexer/co_retrieval.py --selfcheck
```
A run folds in whatever the log gained since the last run and prints the heaviest edges. Weight is a decaying count, `weight = weight * 0.5 ** (days_since_last_seen / 30) + 1`, so a pair seen once today is worth 1, once 30 days ago 0.5, and twice 30 days apart 1.5. Decaying on update from the row's own `last_seen` is what makes an incremental run equal a rebuild: no pass has to touch every row when time passes, and a reader decays from `last_seen` to now the same way. A result set is deduplicated to distinct notes first, since one note matching three sections is one note.

Edges live in `~/.pkm/co_retrieval.db`, beside the log rather than in the vault index, for the reason the log is not in the index either: a reindex rebuilds the index. The table is `(vault, note_a, note_b, weight, last_seen)` keyed on the pair, with `note_a < note_b` so an unordered pair is stored once, and a `log_state` row holding the byte offset already folded in. Byte offset rather than line count because the log is written in text mode, and a half-written last line is left for the next run.

Nothing reads these edges yet. Wiring them into ranking is a separate change and it goes through `eval_rerank.py` first, or it is an opinion rather than an improvement.

### 14. Query Misses (`query_misses.py`)
The query log is the only record of a search that went nowhere, and nothing read it for that. This reads the same `~/.pkm/queries.jsonl` and prints what search did not find:
```bash
python skills/pkm-metadata-indexer/query_misses.py
python skills/pkm-metadata-indexer/query_misses.py --vault brain --window 600
python skills/pkm-metadata-indexer/query_misses.py --selfcheck
```
Three signals. `empty` is a query that returned nothing. `narrow` is a result set that is fewer than four distinct notes: the daemon fills the limit whatever the query, so the row count says nothing about how much was found and the count of distinct notes after deduplication is the only measure there is. `reformulated` groups near-same queries in one vault inside a window, matched on a `difflib` ratio of 0.6 and defaulting to ten minutes, since asking again is the searcher saying the first answer was wrong; `drift` is the Jaccard overlap between the first and last result set of a run, where 1.00 means the rephrase changed nothing and 0.00 means search returned a different set of notes for the same question. A row joins any open run rather than only the previous row, because two questions asked alternately are two reformulations interleaved.

A fourth signal, a top score far under the corpus median, is not built: `log_query` stores result paths and no scores, so the number does not exist to read. It needs a writer change first.

The reader is read-only and replays the whole log from offset 0 each run. It shares `read_new` with `co_retrieval.py`, and so the same tolerance for a half-written last line, but not that module's stored offset, which stays where co-retrieval left it.

Measured on a log of 12 queries over two days, 6 of them distinct: 0 empty, 3 narrow, and 4 reformulation runs covering 10 of the 12. That is a log written almost entirely by daemon tests and watcher probes rather than by anyone searching, so the counts measure the tool and not the index. There is not enough real traffic yet to say what search misses.

### 15. Adding a Corpus
`build_index` is source-agnostic after the scan. Pass `collect=` a function taking a root and returning `(notes, sections, links, errors)` and everything downstream — chunking, hashing, FTS, embedding, RRF, the daemon — works unchanged:
```python
import index_pkm_meta as pkm

def scan_my_corpus(root):
    ...
    return notes, sections, links, errors

pkm.build_index(vault_path=str(root), collect=scan_my_corpus)
```
`index_sessions.py` is the worked example, in 380 lines. The daemon takes the same scanner by import path, so a corpus living in another repository needs no code here:
```bash
python skills/pkm-metadata-indexer/searchd.py --corpus /path/to/that/repo/my_scanner.py:scan_my_corpus=name=/path/to/corpus
```
`MODULE` is a path to a `.py` file or an importable dotted name, `FUNCTION` is the scanner in it, and the rest is the usual `NAME=PATH` vault spec.

Embedding uses CUDA or DirectML when either is present and falls back to CPU. Query embedding is a single vector either way, so the daemon is fast without a GPU; indexing is where the device matters.

### 16. Repository Link Graph (`index_repo.py`)
A repository has no wikilinks and is full of references anyway, so the same `edges` table works on one once the references are derived rather than parsed:
```bash
python skills/pkm-metadata-indexer/index_repo.py --root /path/to/repo
python skills/pkm-metadata-indexer/index_repo.py --root /path/to/repo --with-embeddings
python skills/pkm-metadata-indexer/index_repo.py --selfcheck
python skills/pkm-metadata-indexer/searchd.py --corpus skills/pkm-metadata-indexer/index_repo.py:scan_repo=myrepo=/path/to/repo
```
Every file that is not ignored becomes a note, but only markdown gets sections. A png with no sections is searchable by nothing and is still a row, which is what makes "every image nothing references" one query — the unreferenced side of it is a node no edge points at, not a file nobody listed. `category` is `doc`, `code` or `asset`, so the two acceptance queries are `SELECT source_path FROM edges WHERE resolved_target_path = ?` and `SELECT path FROM notes n WHERE n.category='asset' AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.resolved_target_path = n.path)`. No schema change.

Three reference kinds become edges, all of them read out of markdown: links `[text](path)`, image embeds `![alt](path)`, and bare relative paths in prose such as `see src/auth/token.py`. A target resolves against the source file's directory first, then the repository root, then its filename alone when exactly one file in the repository carries that name, and `resolved_target_path` stays null when none of the three finds anything, which is what makes a broken reference queryable instead of absent. An ambiguous filename stays unresolved, since a wrong edge is worse than a missing one. Urls are skipped. A bare path needs a slash and an extension starting with a letter, or every ratio in the prose reads as a broken reference.

File discovery is `git ls-files --cached --others --exclude-standard`, so `.gitignore` is applied by git rather than by a second half-implementation of it; a directory that is not a checkout falls back to a walk that skips `dist`, `build`, `node_modules` and the rest of `SKIP_DIRS`.

Measured on a 773-file repository with 87 markdown docs, 241 source files and 445 images: the scan takes 0.62s and the whole metadata-only pass 0.74s, for 1,852 sections and 831 edges in 3.7 MB, of which 693 resolve to a real file and 138 do not. 435 of the 445 images are unreferenced, which is the scope showing rather than the repository being untidy: an asset loaded from source code has no markdown reference to find, and imports are not parsed. See [[2026-08-27 a link graph over code, docs and assets]].

### 17. Querying the Link Graph (`link_graph.py`)
The `edges` table is filled by every scanner and read by nothing else, so this is the query surface over it, for a vault index or a repository one:
```bash
python skills/pkm-metadata-indexer/link_graph.py refs src/main.ts
python skills/pkm-metadata-indexer/link_graph.py orphans --ext .png,.webp
python skills/pkm-metadata-indexer/link_graph.py broken --db /path/to/.pkm_index.db
python skills/pkm-metadata-indexer/link_graph.py --selfcheck
```
`refs` lists every document referencing a file, matching a full indexed path or any trailing part of one, so `token.py` finds `src/auth/token.py`. `orphans` lists indexed files with an image extension that nothing points at. `broken` lists references that resolved to nothing. The database is opened read-only, and an index whose `edges` table is empty says so rather than printing an empty list, because an empty result and a missing index otherwise look identical.

An image counts as referenced when an edge matches its path or its basename, not only its resolved target. The vault scanner stores image embeds with a null `resolved_target_path`, so the strict join called all 38 images in a vault orphans. The bias is deliberate: a false orphan gets a file deleted and a false reference only leaves one lying around.

### 18. Antigravity CLI Conversations (`index_agy.py`)
The second scanner over the `collect=` contract, which is what makes section 15 a seam rather than an interface with one implementation:
```bash
python skills/pkm-metadata-indexer/index_agy.py --root ~/.gemini/antigravity-cli
python skills/pkm-metadata-indexer/index_agy.py --probe
python skills/pkm-metadata-indexer/index_agy.py --selfcheck
python skills/pkm-metadata-indexer/searchd.py --corpus skills/pkm-metadata-indexer/index_agy.py:scan_agy=agy=~/.gemini/antigravity-cli
```
`agy` writes one SQLite database per conversation under `conversations/<uuid>.db`, and each row of its `steps` table holds a binary protobuf payload. Prose comes from the field paths in `PROSE_FIELDS` (`19.2` for user turn, `20.1` for assistant turn). Tool calls and file arguments become edges back to touched files.

### 19. Duplicate Notes (`GET /duplicates`)
`--check-duplicate` answers "is this note about to duplicate something" at write time, one title at a time. This is the other half: the whole corpus at once, for the duplicates that were written before the hook existed.
```bash
curl "http://127.0.0.1:44771/duplicates?threshold=0.95&limit=20&vault=brain"
```
Every pair of notes whose pooled vectors are at or above the threshold, unioned into connected components, each component returned once as `{paths, top, unlinked, pairs}` with `pairs` indexing into that component's own `paths`. Clusters are sorted by their highest internal score.

### 20. Co-Commit Graph Mining (`co_commit.py`, `GET /co-commits`, `/similar?graph=1`)
Mines Git commit history to discover serendipitous and implicit relationships between notes that share zero semantic vector similarity (inspired by change coupling and logical coupling research).
```bash
python skills/pkm-metadata-indexer/co_commit.py --rebuild
python skills/pkm-metadata-indexer/co_commit.py --note "profile.md" --top 10 --exclude-hubs
python skills/pkm-metadata-indexer/co_commit.py --selfcheck
curl "http://127.0.0.1:44771/co-commits?note=profile.md&top=10"
curl "http://127.0.0.1:44771/similar?note=profile.md&graph=1"
```
Uses a pure power-law commit scaling model ($w = \max(0.005, 1 / (N - 1)^{1.5})$, no intent multiplier, no time decay — every commit weighted equally regardless of message) with evergreen accumulation. Incremental by default, using `commit_scan_state.last_scanned_sha`; a rewritten history (rebase, filter-repo, force-push) is detected via `merge-base --is-ancestor` and triggers a full rescan. A commit touching more than `MAX_COMMIT_FILES` (200) files is skipped entirely rather than pairwise-weighted: measured against this vault's real history, two bulk-import commits of ~2,476 files each produced 3.13M edge rows, 95.7% of the whole table, all noise.

`--exclude-hubs` drops notes with more co-commit partners than `--hub-degree` (default 20) — a "current project" doc or an AGENTS.md/memory.md-style index file otherwise drags in whatever else that session touched. Measured on real data, unfiltered top edges were 63% redundant or hub noise and 7% genuinely serendipitous; `GET /co-commits` and `/similar?graph=1` both apply it by default, the CLI does not unless asked.

`/similar?graph=1` RRF-fuses `/co-commits` into the vector ranking (`1/(60+rank)` per source, same constant `/search` fuses lexical and vector with), opt-in rather than default: the noise rate above is real even with hub exclusion, so it is a signal a caller asks for. See [[public/co-commit graph mining for serendipitous note associations|co-commit graph mining research]].

## What it extracts
- **Frontmatter metadata:** energy, sentiment, sentiment_labels, tags.
- **Heading-Level Sections:** Sections split by `## ` with line numbers and SHA256 hashes for incremental caching.
- **Neural Embeddings:** 384-dimensional dense vectors (`BAAI/bge-small-en-v1.5`) stored as float32 blobs.
- **Link Graph (`edges`):** All source-to-target [[wikilink|wikilinks]] for instant traversal without grepping files.
- **Co-Commit Graph (`co_commits`):** Weighted Git commit co-occurrence graph for non-textual associative discovery.

## Why use this
Enables instant SQL aggregations and single-turn semantic search across thousands of notes with zero ongoing API costs, serving as an intelligent pre-filter for agents.

### Related
- [[public/pkm-search|pkm-search]]
- [[public/co-commit graph mining for serendipitous note associations|co-commit graph mining for serendipitous note associations]]
- [[agentic tooling upgrades over grep]]
- [[vault hybrid search]]
- [[offline GPU embeddings with incremental cache]]
- [[vault graph traversal]]
- [[token efficient PKM analysis architecture]]
