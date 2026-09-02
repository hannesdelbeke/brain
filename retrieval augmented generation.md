---
aliases:
- RAG
sentiment:
- 5
sentiment-hash: b77c02a5
sentiment-label:
- factual
tags:
- technical
---

connecting the [[Artificial intelligence|AI]] to outside information (e.g. local documents). the model's weights are frozen at training time and its context window is finite, so instead of teaching it your documents you fetch the few passages that answer the question and paste them into the prompt. the generation is "augmented" by retrieval — hence the name.

## the pipeline

1. **chunk** — split documents into pieces small enough to be a useful answer on their own. heading boundaries beat fixed character counts, see [[header extraction for token-efficient retrieval]].
2. **index** — store each chunk for lookup, as keyword terms (BM25), as an embedding vector, or both.
3. **retrieve** — take the query, pull the top-k chunks.
4. **rerank** — optionally re-score that shortlist with a slower, better model before it reaches the prompt.
5. **generate** — paste the surviving chunks into the prompt and let the model answer from them.

## keyword, vector, or hybrid

keyword search (BM25) matches exact terms and is unbeatable when you know the word you want; vector search matches meaning and finds the note that never used your word. neither dominates, so most real systems fuse both and rerank the union — [[2026-08-30 search engines compared to the vector search we use]] compares the options, and [[why BM25 swings by orders of magnitude]] explains why BM25's raw scores can't be compared across corpora.

## the honest limitation

**retrieval is the ceiling.** the generator can only be as right as the chunks it was handed, so a RAG system's quality is a search problem wearing an AI costume, and most disappointing RAG deployments are bad retrieval rather than a bad model. the well-known failure modes: chunks split mid-argument, near-duplicate notes crowding each other out, and the retrieved passage landing in the middle of a long prompt where attention is weakest.

## when not to reach for it

- **the corpus fits in context** — just paste it. a flat digest of a whole personal vault runs around 180k tokens, inside a single modern context window, which is why [[hierarchical map-reduce note rollup]] concluded recursion wasn't needed at that size.
- **the agent can search directly** — an agent with grep and a file reader does retrieval on demand, with the query it actually wants, rather than one embedding guess made ahead of time. an [[MCP server]] exposing search to the model is this shape.
- **the knowledge is stable and central to every answer** — fine-tuning or a system prompt beats re-retrieving the same paragraph on every call. [[model weights vs vector embeddings vs map-reduce]] lays out the three storage choices side by side.

## related notes
- [[model weights vs vector embeddings vs map-reduce]] — where knowledge can live, and the cost of each
- [[2026-08-30 search engines compared to the vector search we use]] — BM25, vector, and hybrid compared
- [[header extraction for token-efficient retrieval]] — chunking on headings, measured token savings
- [[notebookLM]] — a consumer RAG product over documents you upload
- [[2026-08-27 what already exists, prior art for a local hybrid search engine]] — existing local implementations
