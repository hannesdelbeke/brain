---
date: 2026-08-31
created: 2026-08-31
tags:
  - technical
  - search
  - ai
  - vectors
  - multilingual
  - pkm
aliases:
  - multilingual semantic search
  - cross-lingual semantic search
  - multilingual vector search
  - multilingual embeddings in PKM
---

Multilingual semantic search allows querying a vault in one language (e.g. English) and instantly retrieving relevant notes written in another language (e.g. Dutch, French, or German) without translation.

Related: [[public/semantic search|semantic search]], [[public/vector embedding|vector embedding]], [[public/vault hybrid search|vault hybrid search]], [[public/pkm-search|pkm-search]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]

## How cross-lingual vector alignment works

Lexical search engines like SQLite FTS5 or grep compare literal strings. If you query `tax return` in an English search bar, lexical search fails completely against a Dutch note containing `aangifte personenbelasting` because they share zero common characters.

Multilingual vector embedding models (e.g. `paraphrase-multilingual-MiniLM-L12-v2`, `multilingual-e5-large`, or `bge-m3`) project text from multiple languages into a single shared geometric vector space:
- Language tokens are mapped to language-agnostic conceptual coordinates during cross-lingual contrastive training.
- Sentences conveying the same core idea in English, Dutch, French, or Japanese land in close vector proximity.
- Cosine similarity between an English query vector and a non-English note vector remains high, while semantically unrelated notes in any language land far away.

## Empirical benchmark

Cosine similarity for the English query **`"unloading the dishwasher and cleaning the kitchen"`** across different search models:

| Target Note Language | Note Text | Monolingual (`bge-small-en-v1.5`) | Multilingual (`paraphrase-multilingual-MiniLM-L12-v2`) | Lexical / FTS5 |
| :--- | :--- | :--- | :--- | :--- |
| **English** | `unloading the dishwasher and wiping kitchen counters` | 0.8814 | 0.9583 | Match |
| **German** | `den Geschirrspüler ausräumen und die Küche putzen` | 0.6084 | 0.8629 | 0 matches |
| **French** | `vider le lave-vaisselle et nettoyer le comptoir de la cuisine` | 0.5737 | 0.8485 | 0 matches |
| **Dutch** | `de vaatwasser uitladen en het aanrecht schoonmaken` | 0.5730 | 0.7176 | 0 matches |
| **Unrelated Dutch** | `een wandeling maken in het bos met de hond` | 0.5651 | -0.0584 | 0 matches |

Monolingual English models suffer severe cross-lingual degradation: the Dutch translation (0.5730) barely scores above an unrelated Dutch walk in the woods (0.5651). The multilingual model cleanly separates the concept (0.7176 vs -0.0584).

## Monolingual vs multilingual model trade-offs

Choosing the embedding model for a vault indexer involves balancing language flexibility and resource overhead:

**Monolingual models (e.g. `bge-small-en-v1.5`):**
- **Pros:** Smaller model footprint (~130MB ONNX), slightly faster CPU inference, and marginal (~2-4%) accuracy edge on pure English benchmarks.
- **Cons:** Fails to retrieve foreign-language notes unless queried with identical foreign keywords.

**Multilingual models (e.g. `multilingual-e5-small` or `paraphrase-multilingual-MiniLM-L12-v2`):**
- **Pros:** Seamless cross-language discovery across mixed multilingual vaults (English tech notes + Dutch personal/health notes).
- **Cons:** Larger vocabulary size (~250k subword tokens vs ~30k), requiring slightly more RAM and disk cache.

## Hybrid search in mixed-language vaults

In a vault containing mixed-language notes (such as English technical architecture notes and Dutch personal/administrative records), deploying [[public/vault hybrid search|vault hybrid search]] using Reciprocal Rank Fusion (RRF) offers the best combination:
- **Dense multilingual vectors:** Capture conceptual meaning and cross-language intent.
- **Lexical SQLite FTS5:** Captures exact local names, Dutch/German compound words, product codes, and exact technical terms that might get diluted in dense vector space.
