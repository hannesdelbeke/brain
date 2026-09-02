---
date: 2026-08-30
created: 2026-08-30
tags:
  - technical
  - pkm
  - search
aliases:
  - 2026-08-30 search engines compared to the vector search we use
  - BM25 vs vector search vs hybrid search
---

# Search Engines Compared to the Vector Search We Use

This compares keyword search, vector search and web-style search engines against what [[pkm metadata indexer]] actually runs: lexical matching plus a cosine pass, fused by reciprocal rank fusion.

## Keyword search

Keyword search — [BM25](https://dev.to/aloknecessary/bm25-vs-vector-search-choosing-the-right-retrieval-strategy-for-production-systems-599n) being the standard scoring function behind it — matches on the literal tokens in the query. It is exact, cheap, and has no idea what anything means: `agent` matches every note containing that string whether the note is about LLM agents or a real-estate agent. On a large enough notes corpus, the term you'd reach for first can already match a third or more of everything, a match count too wide to be useful regardless of how the match happened. Keyword search is also the only one of the three that's reliable on IDs, filenames, error strings and commit hashes — tokens with no meaning to embed.

## Vector search

Vector search embeds text into a point in a high-dimensional space and ranks by distance, so a query about "why the deploy failed" can match a note that never uses the word deploy. It is the fix for the keyword problem above, at the cost of being bad at exactly what keyword search is good at: [vector search reliably loses to BM25 on exact identifiers](https://aloknecessary.in/blogs/bm25_vs_vector_search/), and even loses to it outright on some specialized domains — financial documents being the benchmarked example — because dense embeddings smear precise terms into approximate neighborhoods.

## Hybrid, which is what this indexer runs

By 2026 the field stopped treating this as a choice: [hybrid retrieval, both methods run and fused, is described as the undisputed default for production RAG](https://denser.ai/blog/hybrid-search-for-rag/) rather than a tradeoff to pick a side of. The fusion method matters more than either retriever alone. BM25 scores are unbounded and cosine similarity is bounded to [-1, 1], so averaging or weighting the raw scores lets BM25 dominate by scale rather than relevance. [Reciprocal rank fusion sidesteps this by only looking at each result's rank position, never its score](https://redis.io/blog/full-text-search-for-rag-the-precision-layer/), which is the same shape of fusion [[pkm metadata indexer]] already runs over its lexical and cosine passes. Reported production numbers put fused recall around 91% at k=10 against 65-78% for either retriever run alone, with the fusion step itself costing single-digit milliseconds — which is why running both is close to free rather than a mode to pick between.

A second-stage cross-encoder reranker sits on top of the fused shortlist in the mature 2026 pipeline, [retrieve, fuse, rerank](https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026). This tool already has that stage as an opt-in `--rerank` flag rather than a default, since it costs real latency per candidate for a measured jump from 32% to 39% precision@10.

## Where a web search engine is a different animal

Google-style web search adds a signal neither keyword nor vector retrieval has on its own: authority and freshness inferred from the link graph and crawl behavior across a corpus nobody controls, PageRank being the canonical example. That axis doesn't apply to a personal vault or a closed corpus — there's no external link graph conferring authority on one note over another, and relevance to the query in front of it is the only ranking signal that means anything. The useful idea to borrow anyway is internal, not external: an `edges(src, dst)` wikilink table gives the same kind of graph a link-authority ranker would use, just scoped to notes that already vouch for each other, which is closer to how a citation network works than a web crawl.

## Bottom line

Nothing here argues for changing the architecture. Hybrid-plus-RRF is both what this indexer already runs and the field's converged answer, arrived at independently. The one open gap the outside research reinforces rather than introduces is reranking-by-default, which is a latency question rather than a design one.

## Related

- [[pkm metadata indexer]] — the tool this note is comparing against the field
- [[retrieval augmented generation]] — feeding an LLM passages fetched at query time instead of training them in
