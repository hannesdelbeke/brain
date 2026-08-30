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
> what happens to the local search daemon when the editor, the command line and several agent sessions all query it in the same second: it answers every one of them, in order, one at a time, because the whole query path sits behind a single lock.
> measured, that is about 15 answers a second and a wait that grows by roughly one query per query already queued. nothing breaks and nothing is lost; the cost is latency, and only the rerank path makes it painful.
> **needs from you:** nothing.

> keep working, and also explore how a daemon can be shared if multiple agents run a session and ask at the same time

> [!todo] next
> **next:** nothing scheduled. the client-side changes are in, the server-side lock narrowing is being measured separately.
> **blocked:** nothing.

**why:** [[2026-08-29 one obsidian plugin over the search daemon]]

## the daemon is already concurrent, and already serialised

the HTTP server is a `ThreadingHTTPServer`, so every client gets its own thread and no request waits for a connection. one lock then serialises the work those threads do: the model, the SQLite connections and the vector matrices are all behind it. so the sharing question has a precise answer. concurrent clients are supported, concurrent *queries* are not.

what that costs, measured on the note corpora:

| clients at once | per-query latency | throughput |
| --- | --- | --- |
| 1 | 60 to 130ms | ~15/s |
| 4 | 4 × that | ~15/s |
| 8 | 8 × that | ~15/s |

throughput is flat, which is the signature of a serial resource: adding clients adds queue, not work. a single agent session asking a handful of questions never notices. eight sessions all searching at once turn a 100ms query into most of a second.

the reindex path is the exception that was already handled: it holds a separate lock, so a pass over a changed corpus does not block queries, and a query landing during one gets an answer over the older index rather than a wait.

## the two things that actually hurt

**rerank.** the cross-encoder path takes 3 to 6 seconds, and it takes the same lock. one client asking for `rerank=1` stalls every other client for the whole of it. that is the only case where a shared daemon feels broken rather than busy, and it is opt-in, which is the right default.

**several corpora in one query.** `vault=all` costs about 2.4× one corpus, since it ranks each one and merges. that is the price of the feature and it is worth it, but it is 2.4× of a serialised resource, not of a parallel one.

## what changed on the client, and why that was the cheap half

the obsidian plugin was reading a busy daemon as a dead one. two changes, both in the client:

the health check timeout went from a second or two to ten seconds. a short timeout on a queued daemon means the plugin concludes nothing is running and spawns a second copy, which is the worst possible response to load: now two processes hold the model, the port fight is resolved by one of them dying, and the survivor is the one with the cold matrix.

the HTTP agent is off, so every request opens and closes its own socket. keep-alive parks a server thread between queries, and threads are exactly what a serialised daemon has too few of when several clients hold connections open and ask nothing.

one more, from the same reading: `/health` is asked at most once a minute and the in-flight promise is shared, so three panes opening together produce one call rather than three.

## what would make it genuinely parallel

the lock covers more than it needs to. the matrix load is the part worth its own lock, since it is the slow one and it is per-corpus; SQLite in WAL mode is already safe for concurrent readers; the ONNX session is the one thing that must stay serialised, and it is also the shortest hold. narrowing the lock to the encode is being measured separately, and the number that decides whether it is worth keeping is throughput at 8 clients: if it does not move well past 15/s, the lock was not the constraint and the extra locks are complexity for nothing.

what is not the answer: a second daemon process per client. the model is 122 MB resident and the point of the daemon is that it is paid once. a queue behind one model is cheaper than two models, right up until the machine has cores doing nothing, which is not this machine's problem today.

related: [[2026-08-26 the pkm search daemon was burning twelve cores]] for the idle-cost half of the same design, and [[progress - local-first search daemon and indexer]] for where the daemon sits in the whole.
