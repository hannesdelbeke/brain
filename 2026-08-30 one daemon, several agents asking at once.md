---
date: 2026-08-30
created: 2026-08-30
tags:
  - search
  - daemon
  - concurrency
  - performance
  - pkm
---

> [!summary] eli5
> what happens to the local search daemon when the editor, the command line and several agent sessions all query it in the same second. it used to answer them one at a time, because the whole query path sat behind a single lock, and eight clients turned a 100ms query into 678ms.
> the lock now covers the shared matrix and nothing else. eight clients went from 7.9 to 39.4 answers a second and from 678ms to 190ms at the median, while a single client is unchanged: nothing was made faster, the queue was removed.
> **needs from you:** nothing.

> keep working, and also explore how a daemon can be shared if multiple agents run a session and ask at the same time

> [!todo] next
> **next:** nothing scheduled. both halves shipped on 2026-08-30, the client timeouts and the narrowed lock.
> **blocked:** nothing.

**why:** [[2026-08-29 one obsidian plugin over the search daemon]]

## the daemon was concurrent and serialised at the same time

the HTTP server is a `ThreadingHTTPServer`, so every client got its own thread and no request waited for a connection. one global lock then serialised the work those threads did: the model, the SQLite connections and the vector matrices were all behind it. concurrent clients were supported, concurrent *queries* were not.

what that cost, and what removing it bought. 48 requests per level against one corpus, a unique query each, median and throughput:

| clients at once | p50 before | p50 after | req/s before | req/s after |
| --- | --- | --- | --- | --- |
| 1 | 102ms | 111ms | 8.8 | 7.7 |
| 4 | 440ms | 107ms | 6.6 | 36.2 |
| 8 | 678ms | 190ms | 7.9 | 39.4 |
| 16 | 1489ms | 276ms | 9.0 | 50.5 |

flat throughput with rising latency is the signature of a serial resource: adding clients added queue, not work. a single client is unchanged after the fix, which is the point — nothing was made faster, the queue was removed.

the reindex path was the exception that was already handled: it holds a separate lock, so a pass over a changed corpus does not block queries, and a query landing during one gets an answer over the older index rather than a wait.

## what the lock actually had to cover

very little, once each claim was checked rather than assumed. every query function opens its own SQLite connection per call, so no connection is shared. the one shared connection belongs to the corpus object and is now the only thing the per-corpus lock protects, along with the vector matrix it hands out. a reindex replaces that matrix with a new tuple rather than mutating it, so a search holding the old one is reading a consistent snapshot, which is what makes releasing the lock before the search legitimate. the ONNX session turned out to be safe to call from several threads: the embed path uses locals plus read-only state, and the tokenizer is Rust taking `&self`.

so the whole query path runs unlocked now, `/links` and `/unlinked` take no lock at all, and the request queue was raised to 64.

one thing the global lock was quietly protecting: the lazy construction of the model and the cross-encoder. two concurrent first callers would each build one, which on a cold machine is a duplicate 90 MB download into the same cache path. that needed its own small lock around the two caches, and it is the only reason the removal was not a pure deletion.

correctness was checked rather than asserted: sixteen simultaneous identical searches returned byte-identical rankings, a reindex alongside eight looping searchers served 1,465 queries with zero failures and one distinct ranking throughout, and the corpus that was not reindexed reported identical counts to the byte afterwards.

**the cost of the change:** a reindex under load went from about 10s idle to 47-53s with eight searches hammering. searches now saturate the CPU the indexer used to get by default. interactive queries winning over a background pass is the right trade, but the watcher feels it.

## the two things that hurt, one of which is fixed

**rerank.** the cross-encoder path takes 3 to 6 seconds. under the global lock, one client asking for `rerank=1` stalled every other client for the whole of it, which was the only case where a shared daemon felt broken rather than busy. it now runs unlocked like the rest, so it costs the caller and the CPU rather than everyone.

**several corpora in one query.** `vault=all` costs about 2.4× one corpus, since it ranks each one and merges. that is the price of the feature and it is worth it, but it is 2.4× of a serialised resource, not of a parallel one.

## what changed on the client, and why that was the cheap half

the obsidian plugin was reading a busy daemon as a dead one. two changes, both in the client:

the health check timeout went from a second or two to ten seconds. a short timeout on a queued daemon means the plugin concludes nothing is running and spawns a second copy, which is the worst possible response to load: now two processes hold the model, the port fight is resolved by one of them dying, and the survivor is the one with the cold matrix.

the HTTP agent is off, so every request opens and closes its own socket. keep-alive parks a server thread between queries, and threads are exactly what a serialised daemon has too few of when several clients hold connections open and ask nothing.

one more, from the same reading: `/health` is asked at most once a minute and the in-flight promise is shared, so three panes opening together produce one call rather than three.

## what is not the answer

a second daemon process per client. the model is 122 MB resident and the point of the daemon is that it is paid once. a queue behind one model was cheaper than two models even before the lock was narrowed, and now there is no queue to escape.

what is still worth knowing: the staleness check walks the corpus and was never under the lock in the first place, so two threads can both walk it and race on the cached answer. the walk is idempotent and last-write-wins, so it is left alone, but "it was protected by the global lock" was not true of it.

related: [[2026-08-26 the pkm search daemon was burning twelve cores]] for the idle-cost half of the same design, and [[progress - local-first search daemon and indexer]] for where the daemon sits in the whole.
