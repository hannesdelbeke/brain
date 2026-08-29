---
aliases:
  - corpora
  - knowledge corpus
  - search corpus
tags:
  - search
  - pkm
  - architecture
  - indexing
---

a **corpus** (plural: *corpora*) is a bounded collection of text, documents or records indexed as one searchable unit, the unit a [[personal knowledge management|PKM]] search engine registers and queries.

in the local-first [[pkm-search]] architecture a corpus sits behind the `collect=` scanner seam: any reader returning a `(notes, sections, links, errors)` tuple can be registered in the resident daemon without changing ranking or storage.

## corpus archetypes

different sources have different ingestion mechanics, update lifecycles and privacy constraints:

- **markdown vaults** ([[Obsidian]], one public and one private): mutable prose and structured notes linked by [[wikilink|wikilinks]], indexed with SQLite FTS5 for BM25 and dense [[vector embedding|vector embeddings]] (`bge-small-en-v1.5`) for meaning, reindexed by debounced file watchers under `searchd --watch`.
- **agent session transcripts** (`~/.claude/projects/`, `~/.gemini/antigravity-cli/`): append-only conversation logs across coding assistants ([[Claude Code]], [[antigravity]], [[OpenAI Codex]]), read with [[2026-08-27 tail reads, resuming an index at the byte it stopped at|byte-offset tail reads]] that drop tool output to keep secrets out of the index, see [[cross-agent session indexing architecture]].
- **git repositories and commit history**: commit messages and file edges read in place, with no copy of the files on disk.
- **repository catalogs and maps**: coarse descriptions and model-written summaries for the repositories of an organisation, enough for coarse-then-deep discovery without cloning any of them.

## multi-corpus isolation and identity

one daemon over several indexes, rather than one merged database or a search server per source:

1. **a shared resident daemon:** one `searchd` on `127.0.0.1:44771` holds the embedding model resident and answers across every registered corpus in 13 to 22ms, with the cross-encoder loaded on first use. the model is corpus-independent, so a process per corpus would pay for it twice.
2. **an index per corpus:** each keeps its own `.pkm_index.db` beside its source files, gitignored and rebuildable, so a corpus stays independently searchable and two histories stay separate.
3. **identity across corpora:** paths are unique only inside one corpus, so a cross-corpus edge is a `corpus:path` pair, `vault:note.md` against `session:uuid.jsonl`, which is what lets [[2026-08-27 a link graph over code, docs and assets]] resolve a reference from one corpus into another and what [[unlinked mentions from the vault index]] reads.
