---
aliases:
  - negative link indexing
  - anti-link R&D
tags:
  - pkm
  - ai
  - graph
  - search
---
Applying [[anti links]] to agentic search and metadata indexing prevents semantic confusion in dense retrieval and graph algorithms.

### Problems Solved

- **Duplicate check false positives:** When creating a note, semantic embedding similarity in `--check-duplicate` can flag homonyms (such as [[text cursor]] vs [[Cursor - The AI Code Editor]]). Anti-links tell the agent the concepts are intentionally separate, skipping false merge suggestions.
- **Graph cluster bridging:** Standard graph algorithms merge clusters when homonyms share an edge. Negative edges prevent false topological bridges.
- **Vector search contamination:** Embedding searches retrieve similar token distributions. Declaring negative constraints prunes false positive notes from retrieval.

### Indexer Adaptations

Integrating anti-links into [[pkm metadata indexer]] and [[agentic tooling upgrades over grep]]:

- **Typed edges in SQLite:** Add an `is_negative INTEGER DEFAULT 0` column to the `edges` table when parsing `anti-links:` frontmatter.
- **Duplicate check suppression:** In `--check-duplicate`, query SQLite for existing negative edges to classify candidates as confirmed distinct concepts rather than duplicates.
- **Negative retrieval filter:** Support query exclusions (e.g. `--exclude-anti <note>`) to penalize anti-linked clusters during hybrid FTS5 and vector ranking.
