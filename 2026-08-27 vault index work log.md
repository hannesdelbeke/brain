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

## Open

- A cross-encoder rerank, now that the model ships with the `fastembed` already installed.
- Section-level SHA256 invalidation, so editing one heading does not re-embed the whole note.
- The write-path near-duplicate gate, still unstarted.
- A second transcript scanner for another agent CLI, which is what turns "one scanner among several" from a claim into a fact.
