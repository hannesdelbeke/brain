---
tags:
  - pkm
  - ai
  - embeddings
---
Vector embeddings and [[semantic search]] don't make [[wikilink|wikilinks]] obsolete. They serve complementary roles:

### Explicit vs Implicit Connection
- **Embeddings** find *implicit similarity* (topic overlap, fuzzy semantic matches). Ideal for discovering connections when exact terms are forgotten.
- [[wikilink|Wikilinks]] define *explicit intent* (causality, hierarchy, sequence, replacement) with an [[explicit link]]. Vector search knows two notes share concepts, but cannot determine whether note A replaces note B or contradicts it.

### Precision for AI Agents and Graphrag
- [[Semantic search]] returns fuzzy top-k matches, which introduces noise across large vaults.
- Graph traversal via [[explicit link|explicit links]] lets [[AI agent|AI agents]] follow exact relationship paths (1-hop / 2-hop dependencies) with 100% precision. Combining both (Hybrid Search / GraphRAG) yields the highest retrieval quality.

### Navigation and Inline Context
- Links act as direct navigation shortcuts within text (e.g. referencing a guide on [[public/offline GPU embeddings with incremental cache|offline GPU embeddings with cache]]).
- Vector search requires querying an external pane or LLM prompt; links stay embedded in the human reading flow.

### Verdict
Vector search removes the burden of manually linking every generic concept. [[wikilink|Wikilinks]] remain essential for structural hierarchy, causal relationships, and precise agent [[note navigation]].
