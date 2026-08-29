---
date: 2026-08-29
created: 2026-08-29
tags:
  - ai
  - search
  - architecture
  - vectors
  - pkm
  - retrieval
aliases:
  - why semantic search fails on recency
  - temporal decay in hybrid retrieval
  - 2026-08-29 temporal decay and entity search in hybrid retrieval
---

# ⏱️ Why Pure Semantic Search Fails on Recency: Temporal Decay and Entity Extraction in Hybrid Retrieval

Why queries like *"recent notes on [Entity / Project]"* break naive vector search engines, and how to combine **lexical entity matching**, **query intent rewriting**, and **exponential time-decay scoring** into a sub-5ms local retrieval pipeline.

Related: [[progress - local-first search daemon and indexer]], [[2026-08-18 what retrieval costs as a vault grows|retrieval economics]], [[cross-agent session indexing architecture]], [[2026-08-29 local search daemon and indexer - release plan and modular decoupling|search suite release plan]], [[2026-08-27 tail reads, resuming an index at the byte it stopped at|tail reads]]

---

## 🛑 The Core Problem: The 3 Blind Spots of Naive Search

When a user searches for *"recent notes on Project Alpha"* or *"what did I write about Alex last week"*, both pure vector search and pure keyword search consistently fail.

```
┌─────────────────────────────────────────────────────────────┐
│             Query: "recent notes on Project Alpha"          │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│   PURE VECTOR (SEMANTIC)    │ │   PURE KEYWORD (LEXICAL)    │
│                             │ │                             │
│ • No concept of "today"     │ │ • Literal word matching     │
│ • 2019 note has same vector │ │ • Misses yesterday's note   │
│   distance as yesterday     │ │   unless it literally has   │
│ • Dilutes proper noun into  │ │   the word "recent"         │
│   generic topic clusters    │ │ • Matches 2021 note saying  │
│                             │ │   "in recent months..."     │
└─────────────────────────────┘ └─────────────────────────────┘
```

### 1. Vector Models Have No Concept of "Now"
Embedding models (like `bge-small-en`, `text-embedding-3`, or `MiniLM`) convert sentences into static mathematical coordinates in high-dimensional space. An entry from 5 years ago about a project update has virtually the **same semantic vector distance** as an entry written yesterday. The embedding has zero awareness of the current calendar date or what relative temporal words (*"recent"*, *"yesterday"*, *"last month"*) mean.

### 2. Entity Dilution in Dense Embeddings
Dense vector spaces represent broad conceptual neighborhoods. Searching for a specific person or project name (`"Alex"` or `"Project Alpha"`) smudges the entity into generic semantic clusters (such as *"team management"*, *"project tracking"*, or *"interpersonal relationships"*). Vector search often returns notes about the general topic where the target entity is never mentioned.

### 3. Keyword Literalism
Standard BM25 or full-text search searches for the literal string `"recent"`. A note created 24 hours ago will be omitted or ranked low if it does not explicitly contain the word `"recent"`, whereas a multi-year-old note containing the phrase *"in recent weeks..."* gets an artificial score boost.

---

## 💡 The 3-Layer Architecture for Temporal Hybrid Retrieval

To resolve entity-recency queries in sub-5ms latency, the retrieval engine applies three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│         User Query: "recent notes on Project Alpha"         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. INTENT & TEMPORAL QUERY REWRITER                         │
│    • Entity: "Project Alpha" (Exact proper noun)            │
│    • Temporal Constraint: date >= NOW() - 7 days            │
│    • Stripped Semantic Payload: "Project Alpha updates"     │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│ 2. EXACT FTS5 ENTITY MATCH  │ │ 3. TIME-DECAY MULTIPLIER    │
│    SQLite: WHERE            │ │    Score × e^(-λ · Δt)      │
│    title LIKE '%Alpha%'     │ │    Recent notes get 3-5x    │
│    OR text MATCH 'Alpha'    │ │    recency boost            │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               └───────────────┬───────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. RECIPROCAL RANK FUSION (RRF) & FINAL RANKING             │
│    Top Results: Exact entity matches sorted by recency      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Formulation: Half-Life Time Decay

Instead of ranking purely on raw cosine similarity or BM25 scores, the retrieval engine computes a composite score modulated by an exponential decay function:

$$\text{Final Score} = \text{RRF}(\text{Score}_{\text{BM25}}, \text{Score}_{\text{Vector}}) \times e^{-\lambda \cdot \Delta t}$$

Where:
* $\Delta t$: Days elapsed since the note's filesystem modification time (`mtime`) or YAML frontmatter date (`date:`).
* $\lambda$: Decay coefficient, calculated from a configurable half-life $t_{1/2}$ (e.g., 30 days):
  $$\lambda = \frac{\ln(2)}{t_{1/2}}$$
* $e^{-\lambda \cdot \Delta t}$: Multiplier scaling from $1.0$ (today) down to $0.5$ (at half-life) and $0.15$ (after 3 half-lives).

Recent notes receive a significant ranking boost, while historical notes must have an exceptionally high semantic or exact lexical score to outrank newer material.

---

## 🛠️ Implementation Pattern in SQLite & Python

### 1. Stripping Temporal Modifiers Before Embedding
In the search daemon, natural-language temporal words are parsed and converted into structured metadata constraints before generating embeddings:

```python
import re
from datetime import datetime, timedelta

TEMPORAL_PATTERNS = {
    r"\b(recent|recently|latest)\b": timedelta(days=7),
    r"\b(yesterday|past day)\b": timedelta(days=1),
    r"\b(last week|past week)\b": timedelta(days=7),
    r"\b(last month|past month)\b": timedelta(days=30),
}

def parse_temporal_intent(query: str) -> tuple[str, datetime | None]:
    clean_query = query
    cutoff_date = None
    
    for pattern, delta in TEMPORAL_PATTERNS.items():
        if re.search(pattern, clean_query, re.IGNORECASE):
            clean_query = re.sub(pattern, "", clean_query, flags=re.IGNORECASE).strip()
            cutoff_date = datetime.now() - delta
            break
            
    return clean_query, cutoff_date
```

### 2. Parameterized SQLite Query with Temporal Bounds
When temporal intent is detected, SQLite executes an exact lexical lookup combined with an `mtime` boundary:

```sql
SELECT 
    path, 
    heading, 
    start_line, 
    mtime,
    bm25(sections_fts) AS bm25_rank
FROM sections_fts
WHERE sections_fts MATCH :entity_query
  AND mtime >= :cutoff_timestamp
ORDER BY mtime DESC, bm25_rank ASC
LIMIT 20;
```

---

## 🤖 Would a Simple Local LLM Be a Better Solution?

A common question in local-first PKM is: *Why build an indexed SQLite FTS5 + ONNX daemon when we could simply run a small local LLM (like Llama 3 8B, Mistral, or Gemma 2 via Ollama) to read notes and answer questions?*

The answer comes down to **retrieval economics, latency, and battery/memory constraints**:

```
┌─────────────────────────────────────────────────────────────┐
│             LOCAL LLM ALONE vs INDEXED DAEMON               │
├───────────────────────┬───────────────────┬─────────────────┤
│ Dimension             │ Local LLM Alone   │ Indexed Daemon  │
├───────────────────────┼───────────────────┼─────────────────┤
│ Search Latency        │ 1,500ms – 6,000ms │ < 5ms (Instant) │
│ Memory / RAM Burden   │ 4GB – 16GB VRAM   │ ~120MB RAM      │
│ Idle CPU / Battery    │ High GPU draw     │ 0.00% idle CPU  │
│ Scalability (10k docs)│ Fails context/scan│ O(1) lookup     │
│ Interactive UI        │ Impossible (lag)  │ Real-time 60fps │
│ Result Precision      │ May hallucinate   │ Exact line & SHA│
└───────────────────────┴───────────────────┴─────────────────┘
```

### 1. The Context & Latency Bottleneck
* A vault with 3,000–10,000 notes contains **5M to 15M tokens**.
* Even a fast local 8B model running on a modern laptop GPU generates ~30–60 tokens/second. Linear scanning across thousands of files is mathematically impossible in real-time.
* For interactive features like the **Obsidian Quick Switcher** or **Backlinks leaf**, results must render in **`< 10ms`** while typing. An LLM generation pass requires 1,500ms–5,000ms minimum.

### 2. The Resource & Battery Footprint
* Keeping a 7B/8B model resident in memory locks **4GB–8GB of VRAM/RAM** continuously and spins GPU cooling fans.
* In contrast, the dedicated search daemon holds a compact NumPy float32 vector matrix in **~120MB of RAM** and operates at **0.000 idle cores** when not actively querying.

### 3. The Optimal Architecture: Local LLM *On Top* of the Index (2-Tier Hierarchy)

A local LLM is not a competitor to the search daemon; it is the **synthesis consumer**:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Prompt: "What did I decide about Project Orion?"    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. TIER 1: INDEXED DAEMON (< 5ms)                           │
│    • Queries FTS5 + ONNX Vectors + Time-Decay Filter        │
│    • Slices 10,000 notes down to TOP 3 EXACT HEADINGS       │
│    • Payload size: ~400 tokens (path, heading, lines)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. TIER 2: LOCAL LLM SYNTHESIS (200ms - 500ms)              │
│    • Local model (Ollama / Claude / Gemini) reads ONLY      │
│      the 400-token payload rather than the entire vault     │
│    • Synthesizes immediate, grounded, hallucination-free    │
│      answer to the user                                     │
└─────────────────────────────────────────────────────────────┘
```

* **Tier 1 (The Retriever / Daemon):** Does the heavy lifting across 10,000 files in <5ms at zero GPU cost.
* **Tier 2 (The Reasoner / Local LLM):** Reads only the distilled top 3 snippets to generate human-readable synthesis.

---

## 🎯 Strategic Summary

| Query / Task Type | Best Tool | Why |
| :--- | :--- | :--- |
| **Interactive Search & Switcher** | **Indexed Daemon (<5ms)** | Requires real-time 60fps keystroke response. |
| **Backlinks & Dead Link Audits** | **SQLite Edges Table (<1ms)** | Pure relational lookup with zero inference overhead. |
| **Multi-Note Synthesis / Summary** | **Local LLM + Daemon RAG** | LLM reads only daemon-filtered snippets (~400 tokens). |

---

## 🔗 Related Notes
- [[progress - local-first search daemon and indexer]]
- [[2026-08-18 what retrieval costs as a vault grows]]
- [[cross-agent session indexing architecture]]
- [[2026-08-29 local search daemon and indexer - release plan and modular decoupling]]
- [[2026-08-27 tail reads, resuming an index at the byte it stopped at]]
