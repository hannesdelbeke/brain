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

## rrf counts votes, so evidence that is not independent wins twice
the formula above sums over a set $M$ of retrieval models, and it is silent about the one thing that has to be true for the sum to mean anything: each ranking has to be an independent opinion. break that and the weaker view wins, because it gets counted more than once. the failure is invisible in the score, which looks like agreement between two systems, and it is invisible in the tests unless a test is written with a note that appears more than once.

**a derived ranking** is the first way to break it. in [[vault hybrid search]] the graph track is seeded from the notes the keyword facets already ranked, so a note found by both was agreeing with itself rather than being confirmed by a second system: a weak one-of-five keyword match collected a vote from each track and beat a note that had matched everything asked of it. the fix is to make the two rankings disjoint, letting the graph vote only on notes the facets did not already find, and to weight the derived ranking below the primary one, at half.

**a retrieval unit finer than the ranked unit** is the second way, and it needs no second system at all. it happens inside a single ranking. if search retrieves sections and you rank notes, a long note occupies several positions in one ranking, and the naive sum reads those as several endorsements. a note holding positions 1, 4 and 6 of one ranking scored nearly three times what one vote at position 1 is worth, which was enough to put a four-section note above a note that had been ranked first on one strong section. the fix is to score each note once per ranking, at its best position.

the general rule is that anything summed over a set of rankings has to be checked for whether membership in one implies membership in another, and whether one row means one candidate. both are cheap to assert and neither shows up as a bug report, because a bad ranking looks like a ranking.

### Related
- [[vault hybrid search]] — Practical application of RRF in Markdown vault search.
- [[vector embedding]] — Dense semantic coordinates used in the vector retrieval pass.
