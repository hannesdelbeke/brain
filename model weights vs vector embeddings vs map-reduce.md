---
aliases:
  - model weights vs vector embeddings vs map-reduce
  - why embeddings and summaries do not replace raw notes
tags:
  - technical
  - ai
  - embeddings
  - rag
  - pkm
---

> [!NOTE]- prompt
> how different is training a [[large language model|LLM]], which under the hood is some kind of vectors.
> vs setting of a [[retrieval augmented generation|RAG]], with [[semantic search]]
> 
> like if i setup a semantic search, which stores semantic links
> and a [[map-reduce]], which stores summaries,
> at what point do i not need the original data anymore?

Training weights, vector embeddings, and hierarchical summaries represent three completely different ways of compressing information. None of them replace the original source notes for personal knowledge.

## How they differ under the hood

### 1. Model weights (Parametric memory)
Training or fine-tuning bakes knowledge directly into neural network weights.
- **Nature:** Implicit, fuzzy, statistical associations.
- **Limitation:** Terrible for exact recall. You cannot easily update a single fact without risking catastrophic forgetting, and models hallucinate when asked for exact dates or obscure quotes.

### 2. Semantic vectors / RAG (Spatial coordinates)
Vector embeddings project text chunks into high-dimensional coordinate space (e.g. 384 numbers via [[pkm metadata indexer]]).
- **Nature:** One-way mathematical hash of meaning.
- **Limitation:** You cannot reverse an embedding back into text. Vectors are purely index pointers; without the original markdown file on disk, vector search has nothing to return.

### 3. Map-reduce summaries (Lossy semantic rollup)
Hierarchical rollups condense thousands of daily notes into monthly and yearly overviews via [[hierarchical map-reduce note rollup]].
- **Nature:** Human-readable abstraction of major events and themes.
- **Limitation:** Highly subjective. Summaries only preserve what seemed important to the model at generation time, permanently discarding specific raw details.

---

## At what point can you delete original data?

**For personal knowledge notes: Never.**

Discarding original notes in favor of summaries or embeddings causes permanent data loss for four reasons:

1. **Embeddings are pointers, not storage:** Vectors don't contain your words. If you delete the note, the vector points to nothing.
2. **Summaries suffer from retroactive bias:** A summary written today discards "minor" details (e.g. a specific symptom, a tool configuration, or a passing comment). Three years later, when that minor detail becomes critical, no summary will have preserved it.
3. **Future AI intelligence gap:** Deleting source notes permanently locks your knowledge base at today's model intelligence. Keeping raw text allows future, smarter models to re-index and extract deeper insights.
4. **Emotional and historical provenance:** As seen in retrospective reviews, summaries tend to sanitize raw emotions and soften conflicts, destroying the ground truth of how you actually felt.

## When discarding raw data makes sense

You can discard raw source data only for high-volume, transient streams where exact wording has zero long-term value:
- Ephemeral scraped web pages or RSS articles.
- Raw terminal build logs and debug traces.
- Automated sensor dumps (e.g. minute-by-minute room temperature vs daily averages).

For human thoughts, project logs, and memories, the raw text is the irreplaceable source of truth; embeddings and [[map-reduce]] summaries are merely navigation layers on top.

## See also
- [[hierarchical map-reduce note rollup]] — recursive batch summarization pipeline
- [[are wikilinks legacy with embedded vector]] — explicit wikilinks vs implicit vector embeddings
- [[pkm metadata indexer]] — local SQLite hybrid search architecture
