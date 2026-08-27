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

a **corpus** (plural: *corpora*) is a distinct, bounded collection of texts, structured documents, or records indexed as a unified searchable dataset in a search engine or personal knowledge management ([[personal knowledge management|PKM]]) system.

in our local-first [[pkm-search]] architecture, a corpus is abstracted behind the `collect=` scanner seam: any reader returning a standard `(notes, sections, links, errors)` tuple can be registered as a corpus in the resident daemon without modifying search, ranking, or storage logic.

## Corpora in the PKM Architecture

different types of data have distinct ingestion characteristics, update frequencies, and lifecycle models:

- **markdown notes vaults** ([[Obsidian]], `brain`): unstructured markdown notes linked via [[wikilink|wikilinks]]. indexed with SQLite FTS5 BM25 for lexical search and dense [[vector embedding|vector embeddings]] (`bge-small-en-v1.5`) for semantic search. updated frequently and reindexed via `searchd --watch` debounced file watchers.
- **agent session transcripts** (`~/.claude/projects`): append-only conversation logs across AI coding assistants ([[Claude]], [[Antigravity]], [[Codex]]). parsed using [[2026-08-27 tail reads, resuming an index at the byte it stopped at|byte-offset tail reads]] that skip tool execution outputs to protect secrets and avoid token bloat. detailed in [[cross-agent session indexing architecture]].
- **repository catalogs & maps**: coarse repository metadata and model-generated summaries enabling coarse-then-deep semantic code discovery across a code organization without full git clones.
- **activity capture streams** (chat discussions, PRs & commits): chronological timeline records of developer activity, commits, and discussions ingested into structured daily digests and searchable logs.
- **documentation & codebase corpora**: domain-specific documentation hubs assembled for agents or evaluation harnesses.

## Multi-Corpus Architecture & Global Node Identity

rather than maintaining separate search servers or vector databases for each dataset:

1. **shared resident daemon:** a single `searchd` daemon running on `127.0.0.1:44771` holds the embedding model and cross-encoder resident in memory, serving queries across all registered corpora in 13–22ms.
2. **isolated local indices:** each corpus maintains its own lightweight SQLite database (`.obsidian/pkm_index.db` or `.pkm_index.db`) containing `notes`, `sections`, `edges`, and FTS5 shadow tables.
3. **global identity across corpora:** while note paths are unique within a single vault, cross-corpus edges use a `corpus:path` global identifier (e.g. `vault:note.md` or `session:uuid.jsonl`) to resolve references across corpora, as designed in [[2026-08-27 a link graph over code, docs and assets]].

## Related

- [[pkm-search]] — local-first hybrid search daemon and metadata indexer
- [[wikilink]] — explicit bidirectional links within and across markdown notes
- [[vector embedding]] — dense semantic representations for cross-corpus similarity
- [[cross-agent session indexing architecture]] — indexing transcript corpora across multiple AI agents
- [[2026-08-27 tail reads, resuming an index at the byte it stopped at]] — incremental indexing for append-only corpora
- [[2026-08-27 a link graph over code, docs and assets]] — unified graph resolution across code, docs, and notes
- [[2026-08-27 synapse links vs wikilinks and semantic links]] — comparing link paradigms across knowledge graphs
- [[unlinked mentions from the vault index]] — discovering unlinked mentions from the FTS5 index
