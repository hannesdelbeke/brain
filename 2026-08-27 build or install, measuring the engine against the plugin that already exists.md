---
date: 2026-08-27
tags:
  - technical
  - search
  - pkm
  - review
  - performance
---
[[2026-08-27 what already exists, prior art for a local hybrid search engine]] found a plugin with the same design as [[pkm-search]]: SQLite FTS5, local embeddings, reciprocal rank fusion, one database at the vault root, served over MCP, with the file watcher we have not built. The obvious follow-up is whether to delete ours and install theirs. This is the review: what a library replaces, what it does not, and both engines measured on the same 3,264 notes.

## The measurement

Obsidian Hybrid Search 0.15.1 against our indexer, same vault, same machine, same day. Both embed to 384 dimensions, theirs `multilingual-e5-small` on CPU through onnxruntime-node, ours `bge-small-en-v1.5` on the GPU through DirectML.

| | theirs | ours |
| --- | --- | --- |
| cold index, 3,264 notes | about 3 notes/s, a measured 1,954 notes in 10m44s | 57.86s total, 131.7 vectors/s |
| reindex with nothing changed | 47s of work, 1m49s wall | 2.57s of work, 4.4s wall |
| database | 25.7 MB, 6,250 chunks, 7,492 links | 28.4 MB, 7,141 sections, 9,702 links |
| one query, fresh process | 2.2s to 2.9s | 1.5s |
| query against a resident process | 8 queries cost the same as 1, so under 50ms each | 17ms warm |

The cold index gap is mostly the device rather than the design. Ours embeds on the GPU; theirs is CPU only, and our parse phase is 3.25s of the 57.86s, so the comparison of the two parsers is 3.25s against whatever share of half an hour is not embedding.

The reindex gap is design. Theirs walks and hashes every file to decide nothing changed, 47s. Ours parses everything and rewrites the tables in 2.57s. Neither is incremental in the sense that matters, which is why the watcher is the next item on both sides of the comparison.

Relevance was not measured. One query each is an anecdote: "how did we stop the laptop overheating" returned a note about building ventilation from theirs, and a note about the laptop itself from ours, and the actual answer is in a session transcript that a vault-only index cannot see. That last part is the argument for two corpora in one index, not an argument about ranking quality.

## What a library would replace

The engine is 2,382 lines outside the tests: 1,473 in the indexer, 521 in the daemon, 388 in the session scanner. The part a hybrid search library replaces is the retrieval math, an FTS5 query, a dot product over a float32 matrix, and a reciprocal rank fusion, which is about 300 lines. The rest is the vault parser, the frontmatter and tag extraction, the link graph, the section chunker, the vector cache keyed by hash, the DirectML batching, the daemon, the query log, and the session transcript scanner.

Swapping the 300 lines for a dependency buys nothing measurable and costs the seams. The chunk boundaries are our heading rule, the payload is `(path, line, heading)` rather than note bodies, and the corpora are pluggable behind `collect=`, which is what makes a transcript and a note the same kind of row.

The reverse question is fairer: adopting the plugin wholesale would mean giving up the transcript corpus, the tool-touched-file edges and the resident daemon, in exchange for a watcher and a cross-encoder. Both of those are available to us as small additions.

## The two libraries worth installing

`watchfiles`, for the watcher. Rust notify bindings, one dependency, replaces a polling loop nobody wants to write. This is the thing the plugin has and we do not.

Nothing, for the reranker, because `fastembed` is already installed and 0.8.0 ships `TextCrossEncoder` with `Xenova/ms-marco-MiniLM-L-6-v2` and `BAAI/bge-reranker-base`. The rerank the plugin advertises as a 570 MB download is an import away.

`sqlite-vec` stays on the shelf until brute force stops being under a millisecond, which it is not close to being at 79,000 sections.

## Outside the plugin shelf

A second survey asked the same question without Obsidian in it. [txtai](https://github.com/neuml/txtai) and [SeekStorm](https://github.com/SeekStorm/SeekStorm) are the closest, both libraries doing lexical, vector and fusion locally in process, and [Infinity](https://github.com/infiniflow/infinity) and [LanceDB](https://github.com/lancedb/lancedb) are the embedded databases with the same three layers plus reranking. On the transcript side, [claude-history](https://github.com/raine/claude-history) turns out to be hybrid rather than fuzzy, with local embeddings over conversation-level routing passages. None of them index a notes corpus and agent transcripts in one ranked index. The full list is in [[2026-08-27 what already exists, prior art for a local hybrid search engine]].

## The other close competitor

`@oomkapwn/enquire-mcp` is the same shape again, BM25 and embeddings fused by reciprocal rank fusion with a BGE reranker, HNSW and int8 quantisation, aimed at Obsidian as agent memory. Two independent projects converging on the same architecture is the useful signal here: the design is right, and being second to it is not a reason to stop.

## The decision, and what came of it

Keep the engine. Both recommendations shipped the same day: `searchd --watch` runs one `watchfiles` thread per corpus, and `--rerank` reorders the fused top 20 with the cross-encoder that was already on disk, at about 22ms per candidate. On the sample query the rerank moved the two sections that answer it from fused rank 9 and 11 to rank 1 and 2, which is the first sign that the ranking gap the plugin's cross-encoder implied was real.

What is still not measured is relevance across a question set rather than one query, and that is the only number that would justify a rewrite rather than an addition.

## How it was run

The plugin's CLI needs a native SQLite module with no prebuild for the current Node, so it was installed against a portable Node 22 rather than changing the machine's toolchain. Index with `reindex`, inspect with `status`, query with `search --json`. The database it writes lives at the vault root and was moved out afterwards so it cannot be committed.
