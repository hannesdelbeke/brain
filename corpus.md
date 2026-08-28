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

A **corpus** (plural: *corpora*) is a bounded collection of text, documents, or records indexed as a unified searchable unit.

In our local-first [[public/pkm-search|pkm-search]] architecture, a corpus is abstracted behind the `collect=` scanner seam: any reader returning a standard `(notes, sections, links, errors)` tuple can be registered in the resident search daemon without changing ranking or storage logic.

## Corpus Archetypes

Different data sources have distinct ingestion mechanics, update lifecycles, and privacy constraints:

- **Markdown Vaults** ([[public/Obsidian vault|Obsidian]], `brain`): Mutable prose and structured notes. Indexed with SQLite FTS5 for BM25 lexical search and dense [[public/vector embedding|vector embeddings]] (`bge-small-en-v1.5`) for semantic search. Incremental changes are tracked via debounced file watchers (`searchd --watch`).
- **Agent Session Transcripts** (`~/.claude/projects/`, `~/.gemini/antigravity-cli/brain/`): Append-only conversation logs across coding assistants. Parsed using [[public/2026-08-27 tail reads, resuming an index at the byte it stopped at|byte-offset tail reads]], dropping verbose tool outputs to protect secrets and avoid token bloat, per [[public/cross-agent session indexing architecture|session indexing architecture]].
- **Git Repositories & Commit History**: In-place commit logs and file edges extracted without duplicating files to disk.
- **Repository Catalogs & Maps**: High-level repository descriptions and summaries enabling coarse-then-deep discovery without cloning entire codebases.

## Multi-Corpus Isolation & Identity

Rather than consolidating heterogeneous datasets into a single database or running separate search servers:

1. **Shared Resident Daemon:** A single local `searchd` daemon holds the embedding and reranking models resident in memory, querying across registered corpora in 13–22ms.
2. **Isolated SQLite Indices:** Each corpus maintains its own lightweight `.pkm_index.db` beside its source files, keeping indexes isolated, rebuildable, and gitignored.
3. **Cross-Corpus Node Identity:** Global identifiers use `corpus:path` namespacing (e.g. `vault:note.md` vs `session:uuid.jsonl`) to resolve references and edges across distinct datasets without path collisions.

