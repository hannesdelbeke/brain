> [!summary] eli5
> BM25's score for a document depends on how rare the query's words are across the whole corpus, so the same query on two different corpora, or two different queries on the same corpus, can produce raw scores that differ by 10x or 100x with no meaning in the number itself, only in the relative order. done, this is the mechanism [[2026-08-31 recency-proximity reranking prior tested against real wikilinks|the recency-proximity note]] cites as elastic's reason for preferring multiplicative boosting over additive.

## the formula

BM25 scores a document for a query as a sum, over the query's terms, of `IDF(term) × termFrequencyComponent`, where `IDF(term) = log((N - n + 0.5) / (n + 0.5) + 1)`, `N` is the total document count and `n` is how many documents contain that term.

## why that swings by orders of magnitude

`IDF` grows without bound as a term gets rarer: a term appearing in 1 of 100,000 documents scores far higher than a term appearing in 50,000 of them, and the growth is logarithmic in a ratio that is itself unbounded, not capped to a fixed range the way a similarity score is.

that means the same document scores wildly differently depending on which words the query happens to contain, and the same query scores wildly differently across corpora with different term-frequency distributions. [elastic's writeup](https://www.elastic.co/search-labs/blog/bm25-ranking-multiplicative-boosting-elasticsearch) gives a concrete instance of this: a base BM25 score of 0.12 on one query, 12 on another, a 100x spread with no change in the boosting logic applied downstream.

## why this matters for combining scores

a fixed additive constant added to BM25 means something completely different depending on which side of that spread the query lands on: elastic's own example is roughly an 18x jump on the low end (0.12 to ~2.12) against a 17% nudge on the high end (12 to 14), for the identical `+2` boost. a multiplicative boost avoids this because a ratio is scale-free — a 20% uplift stays a 20% uplift whichever side of the spread the query score falls on.

not every base score has this problem. vector cosine similarity is bounded to roughly [-1, 1] by construction, independent of corpus term-rarity statistics, so it doesn't carry the swings BM25 does — which is why [[2026-08-31 recency-proximity reranking prior tested against real wikilinks]] found the opposite result (additive safe, multiplicative unsafe) testing a different base score under a different boost shape.
