---
tags:
- pkm
- search
- ai
- graph-theory
- architecture
aliases:
- vector search vs empty stub wikilinks
---
Why creating speculative `[[empty stub links]]` was a pre-vector manual index hack, how modern vector embeddings and full-text search (FTS5) replace manual backlink aggregation, and why empty links pollute knowledge graphs.

Related: [[2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], [[when to request wikilinks from AI]], [[AI-native knowledge formats beyond markdown and git]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[AGENTS.md]]

## Pre-vector origin of empty stub links

In early personal knowledge management tools (Roam Research, Obsidian 2020–2023), search was primitive and limited to exact unranked string matching.

To connect ideas across notes, users wrapped unwritten concepts in double brackets (e.g. `[[Gemini Flash 3.7]]` or `[[neuroplasticity]]`). The goal was to turn Obsidian's backlinks panel into a hand-built inverse index, so future thoughts about an entity would collect in one place. The bracket was doing the job an index should do, because there was no index.

```
┌─────────────────────────────────────────────────────────────┐
│                 THE PRE-VECTOR MANUAL HACK                  │
│                                                             │
│  "tested [[Gemini Flash 3.7]] today" ──┐                    │
│  "latency of [[Gemini Flash 3.7]]"   ──┼──► Backlinks Panel │
│  "benchmarking [[Gemini Flash 3.7]]" ──┘    (Manual Hack)   │
│                                                             │
│  COST: Creates empty ghost node [[Gemini Flash 3.7]]        │
└─────────────────────────────────────────────────────────────┘
```

## Why hybrid search renders stub links obsolete

This vault's own indexer ([[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]) is the reference implementation: `BAAI/bge-small-en-v1.5` embeddings and SQLite FTS5 over the same sections, fused, with an optional `Xenova/ms-marco-MiniLM-L-6-v2` cross-encoder rerank over the top 20 candidates.

- Semantic synonym matching: a query for "fast lightweight Google model" or "3.7 flash benchmarks" surfaces mentions across the vault whether they were written as `Gemini Flash 3.7`, `gemini-3.7-flash`, or `Google small 3.7 model`.
- Exact matching: FTS5 finds every occurrence of a term without manual bracket tagging. A full query on this vault measures 13-26ms, of which the query encode is 3.8-8.6ms; rerank, when asked for, adds about 22ms per candidate.
- No authoring friction: notes get written without stopping to decide whether a passing term deserves speculative brackets.

Fusion plus rerank is the part that replaces the backlinks panel. A manual inverse index returns whatever was bracketed; a reranked hybrid query returns what actually answers the question, including notes written before the entity had a name.

## Pathologies of empty stub links

Creating links to non-existent or empty notes degrades knowledge graph utility:

```
    CLEAN KNOWLEDGE GRAPH               POLLUTED STUB GRAPH
   (substantive concepts)              (stubs as hubs)

       ○ ───────── ○                        ○ ─── ◌ ─── ○
       │           │                        │ ╲ ╱ │ ╲ ╱ │
       ○ ───────── ○                        ◌ ─── ○ ─── ◌
   • every node has a body              • ◌ nodes are empty
   • edges carry meaning                • paths route through nothing
   • multi-hop lands on content         • multi-hop spends tokens on 0 bytes
```

- Stubs become hubs. A term bracketed in twenty notes and written in none is a node with twenty edges and no body, so every path between those notes routes through an empty file. [[2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] describes the same collapse arriving by the other road, over-linking generic words, and the graph view ends up equally unreadable either way.
- Agent retrieval tax: an agent doing multi-hop graph retrieval pays a fetch and some token budget to open a 0-byte note and learn nothing.
- Dead link clutter: speculative links render as broken edges and create unwanted notes on an accidental click.

## Modern rule of thumb

- A canonical note already exists: link it, to record an edge search would not infer on its own.
- Passing mention or tool: plain text. Embeddings and FTS index it either way, and the bracket adds only a node.
- A cluster emerges: once a search turns up five or so notes circling one theme, write the note that theme deserves, then link them.

[[when to request wikilinks from AI]] turns this into instructions for an agent that is drafting notes.
