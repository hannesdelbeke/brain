---
date: 2026-08-30
created: 2026-08-27
tags:
  - progress
  - initiative
  - search
  - vector
  - python
  - technical
status: active
goal: "hybrid search over every corpus on this machine, answered by a resident daemon in tens of milliseconds, with nothing leaving the machine and no cost while idle."
aliases:
  - pkm search progress
---

> [!summary] eli5
> the local search engine behind the vault: one background process holds a small language model in memory and answers "where did we write about X" over the notes, the code repositories and the agent transcripts, in about 20 milliseconds, without sending anything to a server.
> the engine works and is in daily use, and since 2026-08-30 an obsidian plugin sits on top of it with five surfaces. what is open is the link graph over code repositories, and whether either piece gets published at all.
> **needs from you:** open obsidian and look at the plugin, since nobody has seen it rendered. run `index_agy_validation.md` on the machine with a real antigravity history, since the second scanner was written against 18 conversations. then two publishing decisions: whether the engine ships as an installable package under `h-forts/pkm-search`, and whether the plugin repository goes public with a release.

> [!todo] next
> **next:** use the plugin for a week and read what the query log says afterwards, since every number on it so far comes from a harness. after that, point [[index_repo.py]] at a repository of ours and decide whether a code corpus joins the two vaults at logon.
> **blocked:** the plugin cannot be submitted while its repository is private and has no release, which is yours to change.

**why:** [[2026-08-27 agentic pkm action plan]]

the engine is `skills/pkm-metadata-indexer/` in this vault, described in [[pkm-search]], and the day-by-day record of building it is [[2026-08-25 vault index work log]], [[2026-08-27 vault index work log]] and [[2026-08-30 vault index work log]]. this note is the standing state: what works, what is open, and what has been decided so a later session does not reopen it.

> [!warning] a search that ranks well over a stale index looks exactly like one that works
> on 2026-08-28 this corpus had not been indexed since the 25th, nothing was watching it, and a hunt for five notes fell back to six `grep -rn` passes and fifty seconds. the ranking was never the problem, 126 files were simply not in the database. the same shape came back through another door the same day: a reindex held the query lock, a search arriving mid-pass timed out, and the client reads a timeout as no daemon and answers from whatever database the working directory resolves to. every path that gives up quietly answers from the wrong corpus, so each one now says so out loud instead: a `/search` names the files newer than the index, the locks are split, and every result carries its corpus as a prefix.

## what it is

one [[searchd.py]] process on `127.0.0.1:44771` holds the `bge-small-en-v1.5` ONNX model resident, which is what takes the 2 to 5 second pytorch cold start off every query.

each corpus keeps its own SQLite database with `notes`, `sections`, `edges` and FTS5 shadow tables, and a query fuses BM25 with a dense vector search by reciprocal rank, see [[corpus]] for what counts as one. vectors are float32 blobs multiplied in numpy rather than a vector database, which answers in under a millisecond across 68,000 sections and stays the right call below about 300,000 notes.

chunking is by `##` heading, and a result is a location, `(path, line, heading)`, not a body. that is what keeps retrieval affordable for an agent, measured in [[2026-08-18 what retrieval costs as a vault grows]].

two corpora are registered at logon, this vault and the private one, in one process because the model is corpus-independent and a second process pays for it twice.

nothing in the engine imports an assistant SDK. embeddings are local, the interface is plain HTTP, and the source of truth is markdown in git, so any client that can issue a GET can query it.

## what works

the daemon costs nothing while idle. the keepalive encode every 250ms kept ONNX runtime's intra-op pool busy-spinning, one spinner per core, 11.93 of 12 cores on a laptop doing nothing; capping the query path at `QUERY_THREADS = 1` brings a warm idle daemon to 0.000 cores over 20 seconds and costs 3.8ms to 8.6ms per encode, invisible inside a 13 to 22ms query. bulk embedding keeps the whole pool, where the parallelism is real work. a unit test asserts the query path still passes it, because the burn returns silently the moment it stops.

a reindex is incremental in three separate ways: each `##` section is keyed by sha256 so editing one heading re-embeds one section, an append-only transcript is read from the byte the last run stopped at rather than from the top, and a `watchfiles` thread per corpus reindexes on write behind a 2 second debounce. an incremental pass over 859 notes and 5,169 sections is 1.74s with every vector reused, parsing 859 transcripts is 0.78s against 12.46s from the top, and a two-file watch batch is 0.02s. the tail read is written up in [[2026-08-27 tail reads, resuming an index at the byte it stopped at]].

staleness is reported on the query path rather than assumed away. `stale_paths()` walks a corpus in 0.09s over 3,272 files, every `/search` lists what is newer than the last index run, and a reindex starts on a background thread while the answer comes from the index as it stands. a live watcher makes this redundant, which is the point: a dead watcher is silent, and a search is the only thing that will notice.

a reindex no longer blocks a search. the index pass holds its own lock, the two paths share no state, and the database is WAL so a reader keeps its snapshot until the pass commits. under one lock a search arriving mid-pass waited 14.7s against 40ms idle, past the client timeout, which is how it ended up answering from the wrong corpus.

`vault=all` is the default and merges every registered corpus on the fused score. the two vaults stay two indexes so their git histories stay separate and each stays independently searchable; `--db` implies `--direct` and an HTTP error exits non-zero, so a named database can no longer be quietly answered from somewhere else.

the cross-encoder rerank is opt-in and earns its cost when asked for. `Xenova/ms-marco-MiniLM-L-6-v2` reorders the fused top 20 at about 22ms a candidate, 533ms against a 26ms query. [[eval_rerank.py]] asks a hold-out question set twice and a blind judge reads each section without knowing which run produced it: precision@10 39% against 32% over 13 questions on 3,228 notes, and 28% against 22% on 859 transcripts. `--withhold-private` keeps home paths, credentials, LAN addresses and health text out of the judge's input, counted as not useful in both runs.

every `/search` and `/similar` appends a row to `~/.pkm/queries.jsonl` with the query, corpus, latency, result paths and an optional caller-supplied origin. a file rather than a table, because a reindex rebuilds the index and a log a reindex deletes is not a log. it is the producer that co-retrieval and ranking evaluation had none of; the consumer should not be built until it holds weeks of real use.

`--refresh PATH=COMMAND` watches something that is not a corpus and runs a command when it changes, on a 60 second debounce, leaving the watcher up on failure. pointed at the agent transcript directory, an extract that used to run nightly now runs a minute after a transcript is appended to, so what a session recorded this morning is searchable this morning.

the duplicate check runs itself now. `--check-duplicate` existed for weeks and nothing called it, so it is wired to a `PostToolUse` hook on note writes in the private vault and reports what a new note may be duplicating while the agent still has the context to merge or link. it reports rather than refuses, because a write path that can refuse can wedge an unattended nightly run.

the other half of that landed on 2026-08-30 as `GET /duplicates?threshold=`, which sweeps the whole corpus for what was written before the hook existed. it returns connected components rather than pairs, because eleven near-identical notes are 55 pairs of one fact: 46 pairs on this vault become 15 clusters, each carrying `unlinked`, the count of pairs in it with no wikilink, which is what tells a note written twice from a note and its deliberate companion. a threshold scan rather than a filter over the cached `/graph`, since mutual kNN drops the pairs inside a dense pile — measured at k=10, the filter misses 0 of 46 at 0.95, 5 of 200 at 0.93 and 263 of 723 at 0.9. cached on the index version, so 360ms once. nothing in obsidian surfaces it yet.

the transcript corpus has been embedded once and measured: 79,359 sections over 858 transcripts, 298.86s at 265.5 vec/s on DirectML, a 222 MB database, warm hybrid queries at 34 to 62ms against 30 to 58ms lexical, so the ranking is free at query time. the cost is the 122 MB matrix the daemon holds resident, which is why it is not one of the corpora registered at logon today.

an obsidian plugin reaches the daemon over the same HTTP interface any client uses, with five surfaces over one client: a search modal taking regex, semantic, tag, date and missing-link prefixes, a related pane, a semantic local graph, a whole-vault graph on canvas, and a worklist of pairs the index scored as close that nobody linked. it spawns the daemon detached if it is not up, so obsidian closing does not take the CLI's engine with it, and it is desktop-only because the daemon rejects a browser `Origin`. 76 tests against a fake obsidian and a fake daemon, plus a live suite that drives the same views against the running one. described in [[2026-08-29 one obsidian plugin over the search daemon]], the graph it draws in [[2026-08-30 a semantic graph over the whole vault]].

## what is open

the repository link graph works and has not been pointed at our own repositories yet. [[index_repo.py]] landed as v0 on 2026-08-28 and turns markdown links, image embeds, wikilinks and bare relative paths into `edges` rows, with the target left null when it resolves nowhere, which is what makes a broken reference queryable. on 2026-08-30 it was run over obsidian's own documentation repositories, the first ones it has seen with real documentation in them, and three resolver gaps came out of it: extensionless links, wikilinks, and a basename carried by several files. fixed, and 5,586 references over the developer docs now resolve at 97.3% against 3 rows before. "which images are referenced by nothing" returns 729 of 4,457 over the help repository and the sample checks out. designed in [[2026-08-27 a link graph over code, docs and assets]], measured in [[2026-08-30 vault index work log]]. what is left is running it over a repository of ours and deciding whether a code corpus is registered at logon beside the two vaults.

the scanner seam is a fact as of 2026-08-30 and needs confirming on a machine with a real history. [[index_agy.py]] is the second implementation of the `collect=` contract and shares nothing with the first but the return type: antigravity writes one SQLite database per conversation whose step payloads are binary protobuf with no schema published, so there is no line to count and no byte offset to resume from, and the cursor is the step index instead. 18 conversations here, 44 MB, giving 17 notes and 1,511 sections in 2.4 MB, and the daemon takes it through `--corpus` with no code of its own. what is unproven is the field map, which was read off one install by volume, so `index_agy_validation.md` is an eight-step check for an agent to run where there are hundreds of conversations. any summarisation added later posts plain JSON to an endpoint named by an environment variable, with no SDK and no key in the source, and what the model wrote is committed as data so the index rebuilds with no model running.

what remains of [[core Obsidian features to rework on the vault index]] is tag suggestion, orphan-biased random note, and the 1,780 dead wikilinks as a query. the semantic quick switcher and the graph that draws meaning as well as links shipped in the plugin above, and the orphan list was measured and dropped in [[2026-08-30 what else the index can answer]]: 122 orphans is 4% of the vault and sampling them shows stubs that are correctly unlinked.

whether the duplicate gate should ever block rather than report is still a decision, and it needs a week of warn-mode output to answer.

anti-links and negative edge constraints are designed in [[anti links]] and [[anti link RnD]]. Ingestion parses `anti-links:` frontmatter into `edges` with `is_negative = 1`, excluding them from `GET /similar`, suppressing `--check-duplicate` false alarms on homonyms, pruning `/unlinked` false matches, and enabling Rocchio negative vector steering during hybrid search.

`sqlite-vec` has not been benchmarked against the in-process numpy multiply. it only matters for cold queries, which is the case the resident daemon exists to avoid, so it stays last.

## should the engine ship as a package

it was published twice, as this skill directory and as a standalone repository, and the two copies drifted across seven files until a fix landing in one did not reach the other, which is why the idle CPU fix had to be written twice. syncing them holds exactly until the next edit, so on 2026-08-27 one copy was deleted: the standalone repository is a `README.md` pointing here, its git history intact, and consumers find the engine by path through `PKM_SEARCH` or the skill directory.

so the question a release plan reopens is not one copy or two, which is answered, it is whether the one copy gets a distribution channel. if it does, it is generated from this directory by CI and pushed to the empty repository, never hand-maintained beside it, because a hand-maintained second copy is the exact failure already paid for once.

what a release would need that does not exist today: a dependency install that works without the vault around it, and the `--corpus` scanner contract documented as the supported extension point rather than as section 15 of a skill file. the second scanner it also needed exists as of 2026-08-30. the tests exist already.

the three-package version of that, a core library, an obsidian plugin and a searcher over agent transcripts, is worked through in [[2026-08-29 local search daemon and indexer - release plan and modular decoupling]], which sequences the transcript searcher first because it is the only one with a user today.

what it would need to be worth doing: someone other than the author installing it. an obsidian plugin already ships FTS5 plus local vectors plus reciprocal rank fusion over MCP, measured against this engine on the same 3,264 notes in [[2026-08-27 build or install, measuring the engine against the plugin that already exists]] and surveyed in [[2026-08-27 what already exists, prior art for a local hybrid search engine]]. what is ours and not theirs is several corpora in one daemon and tool-touched files as edges, so a release that does not lead with those two is a worse version of something already installable.

## blockers

DirectX 12 driver compilation takes 3 to 5 seconds on the first DirectML startup after a cold boot, before the model enters memory. the keepalive exists so this is paid once.

the FTS rebuild is the floor under an incremental pass. every run deletes and reinserts `sections_fts`, `note_titles_fts` and `edges` whole, 6.6s over 90,000 records, which is now most of the cost. rewriting only the changed paths needs the deletion pass to know which paths a scanner covered, which the scanner interface does not currently say.

further reading: [[offline GPU embeddings with incremental cache]] for the vector cache, [[obsidian search and index slow on 5k notes]] for what this replaces.
