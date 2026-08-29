---
tags:
- pkm
- search
- ai
- graph-theory
- architecture
aliases:
- vector search vs empty stub wikilinks
- why vector search obsoletes speculative linking
- death of empty stub notes
---
Why creating speculative `[[empty stub links]]` was a pre-vector manual index hack, how modern vector embeddings and full-text search (FTS5) replace manual backlink aggregation, and why empty links pollute knowledge graphs.

Related: [[2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], [[when to request wikilinks from AI]], [[AI-native knowledge formats beyond markdown and git]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[AGENTS.md]]

## Pre-vector origin of empty stub links

In early personal knowledge management tools (Roam Research, Obsidian 2020–2023), search was primitive and limited to exact unranked string matching.

To connect ideas across notes, users wrapped unwritten concepts in double brackets (e.g. `[[Gemini Flash 3.7]]` or `[[neuroplasticity]]`):
- **The Goal:** Turn Obsidian's backlinks panel into a manual inverse index to group future thoughts around an entity.
- **The Reality:** A manual compensation for the lack of semantic retrieval.

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

With local vector embeddings and hybrid SQLite search (e.g. `bge-small-en-v1.5` + FTS5):

- **Semantic synonym matching:** A query for *"fast lightweight Google model"* or *"3.7 flash benchmarks"* surfaces mentions across the vault automatically—whether written as `Gemini Flash 3.7`, `gemini-3.7-flash`, or `Google small 3.7 model`.
- **Instant exact matching:** SQLite FTS5 indexes tokens in sub-millisecond time. Querying any term finds all occurrences without manual bracket tagging.
- **Zero authoring friction:** Notes flow naturally without stopping to decide if a passing term deserves speculative brackets.

## Pathologies of empty stub links

Creating links to non-existent or empty notes degrades knowledge graph utility:

```
    CLEAN KNOWLEDGE GRAPH               POLLUTED STUB GRAPH
   (Substantive Concepts)              (Ghost Node Seizure)

       ○ ───────── ○                        ○ ─── ◌ ─── ○
       │           │                        │ ╲ ╱ │ ╲ ╱ │
       ○ ───────── ○                        ◌ ─── ○ ─── ◌
   • High Signal Density                • 70% Nodes are 0-byte Stubs
   • Meaningful Semantic Edges          • Combinatorial Retrieval Noise
   • Fast Agent Multi-Hop               • Lost Context Tokens
```

- **Graph view seizures:** As analyzed in [[2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], empty stub nodes cause hyper-connectivity, collapsing the graph into undifferentiated clutter.
- **Agent retrieval tax:** When an AI agent traverses links during multi-hop graph retrieval, empty stub links waste token budget and latency fetching 0-byte notes.
- **Dead link clutter:** Speculative links produce broken edges and trigger unwanted note creation on accidental clicks.

## Modern rule of thumb

- **Canonical concept note exists:** Create `[[wikilink]]` to establish an explicit, curated edge between substantive knowledge atoms.
- **Passing mention or tool:** Write plain text. Vector embeddings and FTS index it automatically without graph pollution.
- **Emerging cluster discovered:** Once search reveals 5+ notes discussing a recurring theme, create a substantive note and link them.
