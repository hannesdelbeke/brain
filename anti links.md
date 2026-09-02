---
aliases:
  - negative link
  - disambiguation link
  - different from
tags:
  - pkm
  - links
  - graph
origin-sha: e47704a6c
created: 2026-08-22
---

Standard [[wikilink|wikilinks]] define positive associations between notes. Anti-links (negative links) explicitly declare that two concepts are distinct or should not be conflated, preventing false connections in graph views, unlinked mention detectors, and vector search.

## Use cases

- Homonym disambiguation: distinguishing [[Windows]] (the Microsoft OS), [[window]] (glass pane in buildings or cars), and [[window (computing)]] (application GUI window). Also separates [[text cursor]] (typing caret) from [[Cursor - The AI Code Editor]].
- Semantic boundaries: separating similar concepts like Java vs JavaScript, or Python (language) vs python (snake).
- RAG & search pruning: negative constraints for neural search / [[pkm metadata indexer]] to penalize irrelevant clusters.

## Standards & prior art

Major knowledge graph ontologies and wiki engines already establish formal standards for this relation:

- **Wikidata Property P1889 (`different from`):** defined as an item that is different from this item, but could be confused with it (e.g. JavaScript P1889 Java).
- **W3C OWL (`owl:differentFrom`):** formal Semantic Web ontology predicate stating two individuals are distinct entities, preventing reasoners from merging them.
- **Wikipedia hatnotes:** standard `{{Distinguish|...}}` and `{{Not to be confused with|...}}` templates placed at the top of ambiguous articles.

## Implementation options

### Frontmatter metadata (canonical)
Explicit negative edges for indexers and plugins to parse:
```yaml
---
anti-links:
  - "[[Windows]]"
  - "[[window (computing)]]"
---
```
*(Accepts aliases `different_from:`, `different-from:`, `is_not:`, or `is-not:`)*

### Typed inline fields
Using Dataview or typed link syntax:
`different_from:: [[Windows]]`
`is_not:: [[window (computing)]]`

### Wikipedia-style hatnote
A short note at the top of the page for human readers:
> Not to be confused with [[Windows]] (the operating system).

## References
- [[anti link RnD]] — SQLite edge schema, vector steering, and indexer integration
- [[pkm metadata indexer]] — hybrid search and link graph engine
- [[wikilink]] — standard positive graph association
- [[retrieval augmented generation]] — feeding an LLM passages fetched at query time instead of training them in