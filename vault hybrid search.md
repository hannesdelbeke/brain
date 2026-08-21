---
tags:
  - ai
  - search
  - pkm
---
> [!summary] Status
> **Phase 1 Target.** Standard lexical search handles exact keywords well, but combining it with local GPU vector embeddings via RRF solves fuzzy and thematic queries in a single agent turn, saving ~10–12s per search. See [[agentic tooling upgrades over grep]].

Combining lexical keyword matching (BM25) and dense [[vector embedding|semantic vector similarity]] using [[reciprocal rank fusion|Reciprocal Rank Fusion (RRF)]] for Markdown note retrieval.

## The Dual Search Problem
- **Lexical search alone (BM25 / FTS5):** Excels at finding exact function names, hardware models (e.g. `i7-1360P`), acronyms, and unique tags, but fails when queries use synonyms or conceptual phrasing.
- **Semantic vector search alone:** Matches abstract meaning and related concepts (e.g. mapping "sleep latency" to "insomnia"), but struggles with exact alphanumeric identifiers and rare technical jargon.

## Hybrid Pipeline (RRF)
1. **Lexical pass:** Run query against SQLite FTS5 index to score exact text matches via BM25.
2. **Vector pass:** Compute cosine similarity against local sentence-transformers [[vector embedding|embeddings]] cached on GPU per [[offline GPU embeddings with incremental cache]].
3. **Rank fusion:** Merge results using [[reciprocal rank fusion|Reciprocal Rank Fusion]]:
   $$RRF\_Score(d) = \sum_{m \in \{BM25, Vector\}} \frac{1}{k + rank_m(d)}$$
   (where $k \approx 60$).

This guarantees that exact keywords appear at the top while semantically relevant notes without exact wording are pulled into the candidate set.

### Related
- [[vault graph traversal]] — Navigating explicit wikilink structures alongside semantic similarity.
- [[vault MCP server for agents]] — Exposing hybrid search queries directly to AI assistants.
