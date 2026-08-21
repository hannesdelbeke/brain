---
tags:
  - ai
  - search
  - algorithms
---
A score-free rank aggregation algorithm that merges ordered search results from multiple retrieval systems (such as lexical BM25 and dense vector search).

## The Formula
Instead of attempting to calibrate and normalize incompatible similarity scores (e.g. cosine distance vs. BM25 unbounded scores), RRF scores documents strictly by their rank position:

$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + rank_m(d)}$$

- $M$: The set of retrieval models (e.g. `{BM25, Dense Vector}`).
- $rank_m(d)$: The 1-indexed position of document $d$ in system $m$.
- $k$: A constant (typically $k=60$) that smooths the impact of high ranks.

## Why RRF Wins in Hybrid Search
- **Zero score calibration:** Doesn't require calibrating disparate distance metrics.
- **Robustness:** Documents appearing near the top of both keyword and semantic searches receive a strong reciprocal boost, while outliers from a single system drop down naturally.

### Related
- [[vault hybrid search]] — Practical application of RRF in Markdown vault search.
- [[vector embedding]] — Dense semantic coordinates used in the vector retrieval pass.
