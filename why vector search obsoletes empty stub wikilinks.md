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

# Why Vector Search & Hybrid Indexing Obsolete Empty Stub Wikilinks

Why creating speculative `[[empty stub links]]` was a pre-vector manual index hack, how modern vector embeddings and full-text search (FTS5) replace manual backlink aggregation, and why empty links pollute knowledge graphs.

Related: [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks and semantic links]], [[AGENTS.md]], [[public/AI-native knowledge formats beyond markdown and git|AI-native knowledge formats beyond markdown and git]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]

---

## 1. The Pre-Vector Origin of Empty Stub Links

In the early personal knowledge management (PKM) era (Roam Research, Obsidian 2020–2023), search was primitive and limited to exact unranked string matching.

To connect ideas across notes, users adopted the habit of wrapping unwritten concepts in double brackets (e.g. `[[Gemini Flash 3.7]]` or `[[neuroplasticity]]`):
* **The Goal:** Turn Obsidian's **Backlinks** and **Unlinked Mentions** panel into a manual inverse index to group future thoughts around an entity.
* **The Reality:** It was a manual compensation for the lack of semantic retrieval.

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

---

## 2. Why Hybrid Search (Vector + FTS) Renders Stub Links Obsolete

With local vector embeddings and hybrid SQLite search (e.g. `bge-small-en-v1.5` + FTS5):

1. **Semantic Synonym Matching:**
   A query for *"fast lightweight Google model"* or *"3.7 flash benchmarks"* automatically surfaces every mention across your vault—even if you wrote `Gemini Flash 3.7`, `gemini-3.7-flash`, or `Google's small 3.7 model`.
2. **Instant Exact Matching:**
   SQLite FTS5 indexes every token in sub-millisecond time. Querying for any proper noun surfaces all occurrences without needing manual bracket tagging.
3. **Zero Authoring Friction:**
   Writing notes flows naturally without stopping to decide whether a passing term deserves a speculative `[[bracket]]`.

---

## 3. The Pathologies of Empty Stub Links (Graph Pollution)

Creating links to non-existent or empty notes actively damages modern knowledge graphs:

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

* **Graph View Seizures:** As analyzed in [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], empty stub nodes cause hyper-connectivity. The graph view collapses into an undifferentiated ball of yarn where signal is lost in noise.
* **Agent Retrieval Tax:** When an AI coding agent traverses links during multi-hop graph retrieval, every empty stub link wastes token budget and latency fetching 0-byte or trivial stub content.
* **Dead Link Clutter:** Speculative links produce broken graph edges and trigger unwanted note creation on accidental clicks.

---

## 4. The Modern Rule of Thumb

| Scenario | Action | Reason |
| :--- | :--- | :--- |
| **Canonical Concept Note Exists** | **Create `[[wikilink]]`** | Denotes an explicit, human-curated semantic edge between two substantive knowledge atoms. |
| **Passing Mention / Tool / Idea** | **Write Plain Text** | Vector embeddings and FTS index it automatically without graph pollution. |
| **Emerging Cluster Discovered** | **Synthesize a New Note** | Once search reveals 5+ notes discussing a recurring theme, create a real note and link them. |

---

## References
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks and semantic links]] — Comparative taxonomy of knowledge link paradigms
- [[AGENTS.md]] — Vault guidelines forbidding speculative dead wikilinks
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]] — SQLite FTS and dense vector search architecture
