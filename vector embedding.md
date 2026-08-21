---
tags:
  - ai
  - machine-learning
  - search
---
A numerical representation of unstructured text, code, or media as a dense vector of numbers (typically 384 to 1536 dimensions) in high-dimensional space.

## How it Works
Embedding models (e.g. `nomic-embed-text`, `bge-m3`, `text-embedding-3-small`) map semantic meaning to spatial coordinates:
- **Semantic proximity:** Texts with similar conceptual meaning land close together, measured by cosine similarity or dot product.
- **Synonym resolution:** Searches for "insomnia" match documents mentioning "trouble sleeping" even with zero overlapping keywords.
- **Chunking:** Documents are split into paragraphs or sections before embedding, as dense vectors lose precision when averaging multi-page texts.

## Vector Search vs Lexical Search
While vector embeddings excel at abstract conceptual similarity, they struggle with exact alphanumeric identifiers, rare acronyms, and precise code symbol names (where lexical BM25 excels).

### Related
- [[offline GPU embeddings with incremental cache]] — Running local embeddings on RTX GPUs with hash caching.
- [[vault hybrid search]] — Combining vector embeddings with BM25 keyword search.
- [[reciprocal rank fusion]] — Algorithmic fusion of vector and keyword rank lists.
