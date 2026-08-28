---
date: 2026-08-28
created: 2026-08-28
tags:
  - technical
  - pkm
  - search
  - retrieval
  - ai
  - vectors
aliases:
  - semantic search
  - vector search
  - dense retrieval
  - neural search
---

# Semantic Search

**Semantic search** is a retrieval technique that matches documents and queries based on conceptual meaning, semantic intent, and context rather than literal keyword overlap.

In modern [[personal knowledge management|PKM]] and AI retrieval systems, semantic search operates by transforming queries and text sections into dense mathematical vectors ([[vector embedding|vector embeddings]]) using transformer models (such as `bge-small-en-v1.5`), then ranking candidate results by vector cosine similarity.

Related: [[public/vault hybrid search|vault hybrid search]], [[public/vector embedding|vector embedding]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[public/pkm-search|pkm-search]], [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]], [[public/header extraction for token-efficient retrieval|header extraction for token-efficient retrieval]], [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]]

---

## 1. How Semantic Search Handles Markdown Wikilinks (`[[...]]`)

A common concern in Markdown PKM vaults is whether embedding Obsidian wikilinks (e.g. `unloading [[dishwasher]]`) breaks search when queries use plain text (e.g. `unload dishwasher`).

### Empirical Findings:
1. **Wikilink Punctuation Transparency:** Subword tokenizers (BERT, WordPiece, BPE) split brackets `[[` and `]]` into distinct punctuation tokens (`[`, `[`, `term`, `]`, `]`). In high-dimensional vector space, these structural brackets carry negligible semantic weight. The attention layers attend directly to the conceptual words inside.
2. **Morphological Invariance:** The embedding model naturally bridges verb conjugations, suffixes, and tenses (`unload` $\rightarrow$ `unloading`).
3. **Synonym & Paraphrase Matching:** Vector search matches conceptual synonyms without shared keywords (e.g. *emptying* matches *unloading*).

---

## 2. Empirical Benchmark (`bge-small-en-v1.5`)

Live vector cosine similarity measurements for the query **`"unload dishwasher"`**:

| Candidate Text in Note | Cosine Similarity | Match Quality & Behavior |
|:---|:---|:---|
| `"unload dishwasher"` | **1.0000** | Exact verbatim identity |
| `unloading [[dishwasher]]` | **0.9440** | **Near-perfect match (94.4%)** — brackets and `-ing` suffix do not disrupt retrieval |
| `"Kato helped loading and unloading the dishwasher."` | **0.7493** | Strong match across sentence context |
| `"I stopped emptying the [[dishwasher]] regularly recently."` | **0.7450** | Strong match via conceptual synonym (*emptying*) |
| `"doing laundry and washing clothes in washing machine"` | **0.6226** | Baseline distinction (unrelated household chore) |

---

## 3. Retrieval Comparison: Semantic vs. Lexical vs. Exact Grep

| Search Mechanism | Behavior on `unloading [[dishwasher]]` for query `"unload dishwasher"` | Strengths | Failure Modes |
|:---|:---|:---|:---|
| **Exact Substring / Grep** (`ripgrep`) | ❌ **Fails** (literal string interrupted by `[[` and `-ing`) | Sub-millisecond speed; zero index build time | Brittle to typos, suffixes, punctuation, and synonyms |
| **Lexical FTS5 / BM25** (`SQLite FTS5`) | ✅ **Matches** (brackets treated as word boundaries, Porter stemmer matches `unload` $\leftrightarrow$ `unloading`) | Fast, exact keyword recall, low CPU cost | Misses paraphrases and conceptual synonyms |
| **Dense Semantic Search** (`bge-small-en-v1.5`) | ✅ **Matches (0.9440 similarity)** | Captures intent, synonyms, and natural language meaning | Slower inference; can occasionally hallucinate relevance on vague queries |
| **Hybrid Search** (RRF: FTS5 + Dense Vectors) | ✅ **Top-Ranked** | Combines lexical precision with semantic resilience | Requires maintaining a dual index database |

---

## 4. Architectural Best Practices for Vault Indexing

* **Index at the Section Level:** Embed heading-level sections rather than averaging entire multi-thousand-word documents. See [[public/header extraction for token-efficient retrieval|header extraction for token-efficient retrieval]] and [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]].
* **Deploy Hybrid Reciprocal Rank Fusion (RRF):** Combine SQLite FTS5 lexical ranking with dense vector similarity to guarantee both exact identifier lookups and fuzzy semantic concept discovery. See [[public/vault hybrid search|vault hybrid search]].
* **Preserve Native Wikilinks:** There is no need to strip `[[...]]` markup prior to vector embedding; modern embedding models handle native Markdown syntax natively.
