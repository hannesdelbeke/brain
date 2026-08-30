> [!summary] eli5
> two proposals for the vault's search tooling: query the vectors from inside SQL so a filter and a nearest-neighbour search happen in one statement, and sync raw transcripts between machines rather than replicating the index.
> neither is built. the sqlite-vec half is already decided against for now in [[progress - local-first search daemon and indexer]], which parks it behind a benchmark, so what is live here is the filtering argument and the whole cross-machine section.
>
> **needs from you:** nothing

> also search related content online like research or github repos or articles. link in notes or new notes

**why:** [[offline GPU embeddings with incremental cache]]

[[offline GPU embeddings with incremental cache]] already does the sane thing for this vault's size, and [[cross-agent session indexing architecture]] already surveys the session-memory landscape, so this note only adds what a fresh pass turned up that those two did not cover.

## filtered KNN inside SQL, not python-side cosine

the standing decision is in [[progress - local-first search daemon and indexer]]: [asg017/sqlite-vec](https://github.com/asg017/sqlite-vec) has not been benchmarked against the in-process numpy multiply, it only matters for cold queries, which is the case the resident daemon exists to avoid, so it stays last. speed is not the argument and this note does not reopen it.

the argument that is not in that note is filtering. the embeddings note's option B keeps vectors as raw BLOBs and compares in numpy, so a `WHERE tag = 'technical'` or `WHERE path LIKE 'learnings/%'` needs a second pass in python around the search. a `vec0` virtual table carries the predicate and the `vec_distance_cosine()` in the same statement instead. that is the reason to swap the BLOB column, if it is ever swapped, and it is worth measuring alongside the cold-query number rather than instead of it.

real ANN indexing is not the move at any point soon. sqlite-vec has [no ANN index as of early 2026](https://github.com/asg017/sqlite-vec/issues/25) by design, the author's position being that most local-AI corpora are thousands to hundreds of thousands of vectors and brute force wins there. this vault is at 17,356 sections. if the index ever crosses roughly a million vectors, which would need the session transcripts plus the markdown vault plus every code repository on this machine indexed at once, [Vec1](https://sqlite.org/vec1) from the SQLite team or [vectorlite](https://github.com/1yefuwang1/vectorlite) (3x-30x faster than sqlite-vec's brute force in its own benchmarks, at the cost of exactness) are the names to reach for then.

## syncing the session index across machines: sync the source, not the database

[[cross-agent session indexing architecture]] lists cross-machine sync as an open task, and the transcripts it indexes stay wherever `~/.claude/projects` or the antigravity and codex equivalents happen to live on that one machine. the instinct is to replicate the sqlite index with [Litestream](https://litestream.io/) (streaming WAL replication to a file or S3) or [rqlite](https://github.com/rqlite/rqlite) (raft-clustered sqlite for real multi-writer distribution), both current in 2026 and both wrong here. the index is a rebuildable cache over the transcripts, the same markdown-as-source, sqlite-as-compiled-bytecode split [[2026-08-26 trending github repos]] argues for, and the tail-read design in [[2026-08-27 tail reads, resuming an index at the byte it stopped at]] means a second machine rebuilds from scratch in seconds once the raw jsonl is there, not the 298s embedding pass the first machine paid once.

so sync the raw transcript files by whatever channel already exists, a private git repo, syncthing, a scheduled rsync, and let each machine rebuild its own index. CRDT options like [cr-sqlite](https://github.com/vlcn-io/cr-sqlite) or [sqlite-sync](https://github.com/sqliteai/sqlite-sync) are worth remembering if two machines ever need to see each other's ongoing sessions live rather than after the fact, which is a different requirement from the one written down.
