---
tags:
  - ai
  - graph
  - obsidian
  - pkm
---
> [!summary] Conclusion
> **Not needed right now.** Obsidian's native graph view and local backlinks provide enough navigation utility. Maintaining an external graph database or networkx index introduces maintenance overhead for marginal gains.

Indexing and traversing explicit [[wikilink|wikilinks]] to discover multi-hop conceptual neighborhoods, backlinks, and bridges across notes.

## How it Works
Unlike keyword search which treats notes as isolated documents, graph traversal treats the vault as a directed network, a [[graph theory|graph]]:
- **Index:** A lightweight SQLite table (`links: source, target, link_type`) or in-memory `networkx` graph populated from regex matches (`\[\[([^\]|#]+)\]\]`).
- **Multi-hop expansion:** Queries immediate neighbors ($N=1$) and 2-hop context ($N=2$) to surface related notes that don't share exact keywords with the starting note.
- **Shortest path:** Finds the shortest chain of reasoning connecting two disparate concepts.

## Core Operations

```bash
# Expand 2-hop conceptual neighborhood around a note
vault-graph context "wikilink temporal integrity" --depth 2

# Find shortest reasoning chain connecting two notes
vault-graph path "2026-04 stroke" "productivity on society"

# Identify isolated or weakly connected cluster nodes
vault-graph orphans
```

### Related
- [[extract historic wikilinks from git]] — Mining link additions and deletions across Git revisions into SQLite.
- [[vault hybrid search]] — Combining explicit link traversal with semantic vector similarity.
