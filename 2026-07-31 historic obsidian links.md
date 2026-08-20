---
tags:
  - ai-assisted
  - technical
  - artificial-intelligence
  - obsidian
  - git
  - pkm
---
> [!question]
> [[Obsidian]] displays active links, backlinks, and unlinked mentions, but ignores **historic links** that were removed during note refactors. That data still exists in [[git]] history. Does extracting historic links provide value for AI note parsing and knowledge graphs?

### Value of Historical Link Data
- **Conceptual drift:** Tracks how topics shifted or split over time.
- **Recovering lost context:** Identifies accidental link removals or ideas that were once related before a refactor.
- **Denser graph retrieval:** Graph models (GraphSAGE, temporal GNNs, GraphRAG) perform better on denser graphs. Temporal edges increase graph density, yielding richer embeddings and context.
- **Edge half-life ranking:** The duration a link survived acts as a natural decay and relevance weighting signal for RAG ranking.

### Dependency on Commit Granularity
Value depends on commit frequency. Batch commits (e.g. daily automated syncs) merge changes into coarse snapshots, losing individual edit context. Fine-grained commits allow exact temporal reconstruction:

```bash
git log --oneline -- '*.md' | wc -l
```

proposed solution: [[extract historic wikilinks from git]]

### References
- [[wikilink temporal integrity]] — resolves links to their historical snapshot states based on commit timestamps.
- [[linking to git commits and diffs in obsidian via uri]] — inspecting historical diffs via URI protocol.
