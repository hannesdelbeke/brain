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

## Problems solved

- Duplicate check false positives: semantic embedding similarity in `--check-duplicate` can flag homonyms like [[text cursor]] vs [[Cursor - The AI Code Editor]]. Anti-links confirm concepts are intentionally distinct, skipping false merge warnings.
- Graph cluster bridging: standard graph layouts pull connected nodes together. Homonyms create false bridges across unrelated knowledge clusters.
- Vector search contamination: dense embedding models retrieve similar token distributions. Negative constraints prune false positive clusters from retrieval.
- Unlinked mention noise: prevents false suggestions in `/unlinked` when a term is mentioned in the context of an unrelated homonym.

## Indexer architecture

Integrating anti-links into [[pkm metadata indexer]] and [[agentic tooling upgrades over grep]] spans four layers:

### SQLite edge schema
Add polarity to the `edges` table:
```sql
edges (source_path, target_raw, resolved_target_path, is_negative INTEGER DEFAULT 0)
```
Frontmatter `anti-links:` or inline `is_not:: [[Target]]` tags are stored with `is_negative = 1`. Standard link traversals filter by `is_negative = 0`, while constraint filters query `is_negative = 1`.

### Vector steering and reranking
Dense retrieval maps words with similar token distributions close in latent space. Anti-links apply Rocchio negative vector steering:

$$\vec{q}_{\text{steered}} = \vec{q} + \alpha \vec{v}_{\text{target}} - \beta \sum \vec{v}_{\text{anti-link}}$$

Subtracting the anti-linked embedding pushes query vectors away from the confusing cluster before computing cosine similarity. In cross-encoder reranking, candidates carrying negative edges receive a score penalty.

### Nearest notes and duplicate suppression
- `GET /similar?note=A` strictly excludes anti-linked documents from the top-$k$ nearest neighbors, keeping local semantic graphs clean.
- `--check-duplicate` queries SQLite for negative edges. If an anti-link exists between candidate notes, the duplicate warning is suppressed.

### Graph repulsion and unlinked mentions
- In force-directed graph layouts, anti-links act as repulsive springs, pushing distinct clusters apart.
- `/unlinked?note=A` ignores sections in notes that explicitly declare `anti-links: [[A]]`.

## References
- [[anti links]] — conceptual definition and use cases
- [[pkm metadata indexer]] — hybrid SQLite and vector indexer skill
- [[agentic tooling upgrades over grep]] — deterministic index-driven agent search
- [[vault hybrid search]] — BM25 and neural embedding fusion
