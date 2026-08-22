---
aliases:
  - negative link
  - disambiguation link
tags:
  - pkm
  - links
  - graph
origin-sha: e47704a6c
created: 2026-08-22
---
Standard [[wikilink|wikilinks]] define positive associations between notes. Anti-links (negative links) explicitly declare that two concepts are distinct or should not be conflated, preventing false connections in graph views, unlinked mention detectors, and vector search.

### Use cases
- **Homonym disambiguation:** Distinguishing [[text cursor]] (caret), mouse pointer, and [[Cursor - The AI Code Editor]].
- **Semantic boundaries:** Separating similar concepts like Java vs JavaScript, or Python (language) vs python (snake).
- **RAG & Search pruning:** Negative constraints for neural search / [[pkm metadata indexer]] to penalize irrelevant clusters.

### Implementation options

**Wikipedia-style hatnote**
A short note at the top of the page:
> Not to be confused with [[text cursor]] or [[mouse cursor]].

**Frontmatter metadata**
Explicit negative edges for indexers and plugins to parse:
```yaml
anti-links:
  - "[[text cursor]]"
  - "[[Cursor - The AI Code Editor]]"
```

**Typed inline fields**
Using Dataview or typed link syntax:
`is_not:: [[Cursor - The AI Code Editor]]`

This prevents homonyms from creating artificial bridges between unrelated clusters in your knowledge graph.

For indexing and search integration with SQLite and vector embeddings, see [[anti link RnD]].