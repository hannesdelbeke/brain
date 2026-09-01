---
tags:
  - technical
  - obsidian
  - search
  - pkm
---
A day of work on the search engine, following [[2026-08-25 vault index work log]]. The theme is the gap between what the notes claimed and what the code did: an audit checked one against the other, and most of today was closing the differences it found. Written so a later session can pick up without rereading the transcript.

## The engine has one home now

It was published twice, as `skills/pkm-metadata-indexer/` here and as a standalone repository, and the copies had drifted across seven files with two tools existing only here. That is why the CPU fix below had to be written twice. Syncing them was tried first and holds exactly until the next edit, so one copy was deleted instead: the standalone repository is now a `README.md` pointing at the skill, and its git history stays where it is.

The skill absorbed the two things only the other README carried, the custom scanner contract for `--corpus` and the GPU fallback note, as section 13. Consumers find the engine by path, either `PKM_SEARCH` or the skill directory. See [[pkm-search]].

## The idle CPU burn, fixed

The keepalive thread encodes a throwaway string every 250ms so the model never goes cold. ONNX Runtime's intra-op pool busy-spins between those ticks, one spinner per core, so the cost scaled with the machine rather than with the work: 11.93 of 12 cores on a laptop doing nothing.

`QUERY_THREADS = 1` on the query path only, with `threads` in the model cache key, brings a warm idle daemon to 0.000 cores. Bulk embedding keeps the full pool, where the parallelism is real work. The cost is 3.8ms to 8.6ms per encode, invisible inside a 13-22ms query.

The fix written up before this one, an `ort.SessionOptions` carrying `session.intra_op.allow_spinning=0`, was never reachable: `fastembed.TextEmbedding` accepts no session options, and its `threads=` argument reaches the same pool. That is why the burn survived being documented as fixed.

Keepalive is now on by default, since the reason to avoid it is gone. `--no-keepalive` turns it off and trades about 30ms on the first query after idle.

## Query logging, the producer that was missing

Every `/search` and `/similar` appends one JSON Lines row to `~/.pkm/queries.jsonl`: timestamp, vault, query text, limit, latency and the result paths, plus an `origin` the caller can pass as `&origin=<note>` to say where the search came from. `/similar` records the note as its own origin.

A file rather than a table in the index, because a reindex rebuilds the index and a log a reindex deletes is not a log. Scores are left out, since they are reproducible from the query; the paths are what a co-retrieval edge needs. `--no-query-log` turns it off, which is the switch to reach for given the file holds query strings in plain text.

This is the write path [[2026-08-27 every read is a write - co-retrieval as synapse strength]] designed and the whole Hebbian branch of [[2026-08-27 agentic pkm action plan]] was deferred for. The consumer does not exist yet, and should not be built until the log holds a few weeks of real use.

## Session embeddings are on

The transcript corpus was lexical only. A full pass with `--with-embeddings` generated 79,359 vectors over 858 transcripts in 298.86s at 265.5 vec/s on DirectML, 320.92s and 222 MB in total.

Warm hybrid queries answer in 34-62ms against 30-58ms lexical, so the ranking is effectively free at query time; the cost is the 122 MB vector matrix the daemon holds resident. The test that shows why it was worth it: "how did we stop the laptop overheating" returns the session that diagnosed the CPU burn as its first hit, sharing no keyword with the query.

Everything was re-embedded because nothing was cached, which is the argument for the byte-offset resume still open below.

## Measuring a ranking change instead of eyeballing it

On a non-vault corpus of 606 documents, a model rewrote 572 thin one-line summaries, on the theory that the coarse pass was ranking on boilerplate. A blind judge A/B says it did not work: precision@10 21% against 22%, precision@3 38% against 38%, first useful result at rank 1.7 either way. The sentences read better and rank the same.

Two things are worth keeping from that. The harness, which serves two corpora over the same source with and without the change and has a model judge each result from the source document alone, so the judge cannot reward the text being changed. And the discipline of splitting the questions into the ones used while building and the ones written afterwards, because a question already looked at is not evidence.

The other lesson was procedural and expensive: the first measurement was run against a stale index. The daemon imports its scanner at startup, so `POST /reindex` rebuilt with the pre-edit scanner and the new text was never in the queried database. A daemon restart is part of changing a scanner.

## Reindexing the transcripts is a tail read now

A transcript only grows, so each run records the byte it stopped at and the next one parses what was appended, taking the rest of the rows back out of the index rather than a second copy on disk. Parsing 859 transcripts drops from 12.46s to 0.78s and the whole metadata-only pass from 19.24s to 7.78s, of which 6.6s is the search tables being rebuilt from scratch, which is the floor now.

A shrunk file, a moved prefix hash, or a section count that disagrees with the index reads in full, and the bookmark file carries a hash of the scanner's source, so editing the parser invalidates every offset instead of serving rows the old parser wrote. Written up in [[2026-08-27 tail reads, resuming an index at the byte it stopped at]].

## The competitor, installed and run

A survey found an Obsidian plugin shipping the same design, so it was installed and both engines were pointed at the same 3,264 notes. Cold index 57.86s for ours against about half an hour for theirs, which is mostly DirectML against CPU. A reindex with nothing changed 2.57s against 47s, which is not the device. Databases 28.4 MB against 25.7 MB, a query from a cold process 1.5s against 2.2s, and both answer in tens of milliseconds once a process is warm.

Relevance was not measured and one query each proves nothing, except incidentally: neither vault-only index can answer "how did we stop the laptop overheating", because the answer is in a transcript. A library would replace about 300 of the 2,382 non-test lines. The full accounting is in [[2026-08-27 build or install, measuring the engine against the plugin that already exists]]; what gets taken from it is `watchfiles` for the watcher and `fastembed`'s `TextCrossEncoder`, which is already installed, for the rerank.

## The index follows writes now

`searchd --watch` runs one `watchfiles` thread per corpus, so a save reindexes that corpus a couple of seconds later. Changes batch over a 2s debounce, so five files saved together are one pass, and a pass that throws prints and leaves the watcher running.

The one thing that had to be got right is that a reindex writes the database inside the root it is watching, which would trigger the next reindex forever. The filter drops the database, its journals and every dotfile, none of which a note is ever named. Measured live: a two-file batch reindexes in 0.02s, and the whole-vault pass with nothing to re-embed is 2.57s, so the ceiling is a couple of seconds either way.

## Except it did not, until the cache was fixed

Added 2026-08-28. The watcher above was written and correct and no reindex it ran ever reached a search. Nor did a manual one: `POST /reindex` returned `{"notes": 816, "sections": 3265}` and the next query answered out of the pre-edit index. The database was right; the daemon's resident vector matrix was stale.

`Vault.matrix()` opened a fresh SQLite connection per call and used `PRAGMA data_version` as the invalidation signal. A fresh connection reads 2 and keeps reading 2 no matter what any other connection commits — the counter only moves for a connection that was already open when the write landed. Measured: three fresh connections read 2, 2, 2 across two external commits, while one long-lived connection went 2 to 3. So the cache was pinned for the life of the process and every watcher pass, every manual reindex and every plugin write was invisible.

The connection now lives on the `Vault` with `check_same_thread=False`, which is safe because every caller already holds `LOCK`, and a `close()` came with it because Windows will not delete a database file a test still has open. [[test_searchd.py]] asserts a reindex changes `vectors_version`.

Two things generalise. A cache whose invalidation is never exercised by a test is a cache that is always warm and always wrong, and this one sat behind a docstring that described the mechanism accurately while using it incorrectly. And it is the second time in two days that the daemon served a stale answer with a correct database behind it, after the scanner-restart trap above — the pattern is that the process is the cache, so anything measured against a long-running daemon needs a restart or a proven invalidation before the number means anything.

Also worth separating a written feature from a running one. `--watch` is a flag, and the daemons on this machine were started without it, so the index was as fresh as the last reindex somebody remembered. Detecting staleness at query time was considered instead and rejected: it puts a stat walk of the whole root on the latency path of a 13-22ms query, and reindexing in the background after answering means learning the answer was stale only after giving it.

## The rerank, and the first sign the ranking was leaving something behind

`--rerank` on the CLI and `&rerank=1` on the daemon reorder the fused top 20 with `Xenova/ms-marco-MiniLM-L-6-v2`, which ships inside the `fastembed` already installed, so it cost no dependency and a 90 MB download on first use. The model is loaded lazily and never touched otherwise.

It is opt-in because it is slow: about 22ms per candidate, so 227ms at 10 candidates, 533ms at 20 and 706ms at 30, against a 26ms query. Twenty is the default because of what the sample query showed. "how did we stop the laptop overheating" put the two sections that actually answer it at fused rank 9 and 11, under notes about laptop hardware and building ventilation; the rerank put both first, at 5.9 and 5.4 against -5.2 for the next one. A top-10 rerank would have found one and missed the other.

One query is not an evaluation, and the next step was the same question set discipline used on the summaries.

## The rerank, measured

[[eval_rerank.py]] asks one question set of one corpus twice, with the rerank and without, and a model judges each returned section from the section text alone, never seeing which run produced it or at what rank. Fourteen questions written before any result was looked at, one of them the query the rerank was built on, 3,228 notes, 178 judgements, ten minutes.

Over the thirteen hold-out questions precision@10 is 39% with the rerank against 32% without, 51 useful sections against 41, and the first useful section sits at mean rank 1.6 against 1.9. Seven questions improve, three get worse, three are unchanged. So the rerank is worth its 533ms, and the size of the win is a couple of extra useful sections in ten rather than a different result list.

Two things the numbers say that the anecdote did not. The rerank often pushes the first useful section from rank 1 to rank 2 while adding useful sections further down, which is what a reorder over a twenty-candidate pool does: it trades the top of the list for the body of it. And it can lose a question outright, as it did on the audit question, going from one useful section to none.

The question the rerank was built on, "how did we stop the laptop overheating", scores zero on both arms here, because the sections that answer it are in the transcript corpus and this run was against the vault.

## The transcripts, measured without handing over the private parts

The transcript corpus is where the rerank was supposed to matter most and it is also the corpus a judge running elsewhere should not read in full. What a run would have sent was counted first: 145 sections, 77,831 characters, over 66 transcripts, holding home paths, work repository and channel names, a home automation server address and a personal email, and no keys, no tokens, no LAN addresses and no phone numbers.

So `--withhold-private` keeps a section here rather than sending it, on patterns for home paths, credentials, LAN addresses, contact details, house automation and health or money words. It held back 63 of the 145, 55 of them for a home path alone, because a transcript is mostly shell commands. A withheld section counts as not useful in both runs, which keeps the comparison fair and pushes the absolute numbers down, so the report also scores over the sections a judge actually saw.

Over the same thirteen hold-out questions, 859 transcripts and 79,645 sections: precision@10 28% with the rerank against 22% without, 46% against 34% over judged sections, first useful section at mean rank 2.9 against 3.9, and eleven of thirteen questions answered against ten. The margin is wider than on the vault, which is the corpus argument in one line: the longer and more repetitive the documents, the more a reorder that reads the query and the passage together is worth.

The question the rerank was built on lands differently under a blind judge than it did by eye: three useful sections with the rerank against one without, but the first useful one at rank 4 rather than rank 1. The reorder wins the list and loses the top of it, the same trade the vault run showed.

## Section-level invalidation was already in

Editing one heading does not re-embed the whole note, and has not since commit `f50d2ce8` on 2026-08-21. [[index_pkm_meta.py]] hashes each `##` section into `Section.sha256`, `load_vector_cache()` keys reuse on `(sha256, embedding_model, chunking_version)`, and `test_unchanged_section_keeps_cached_vector` fails if an untouched section loses its vector or an edited one keeps it. It was carried on the open list here and in [[public/progress - local-first search daemon and indexer|the progress note]] for a week after it shipped, because it landed inside a commit named for per-batch SQLite checkpointing.

What that leaves is a different floor than the one the open item assumed. On 859 notes and 5,169 sections an incremental run is 1.74s: 1.20s scanning and parsing every file, 0.45s in SQLite including the whole-table `DELETE FROM sections_fts`, `note_titles_fts` and `edges` rebuild, and embedding at effectively zero. Cutting the FTS and edges rebuild to a delta wins at most 0.45s of that, so the lever worth pulling first is skipping unchanged files on the scan.

## Open

- The write-path near-duplicate gate, still unstarted.
- A second transcript scanner for another agent CLI, which is what turns "one scanner among several" from a claim into a fact.
