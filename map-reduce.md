---
tags:
  - architecture
  - algorithms
  - ai
  - data
---
A distributed processing model for processing large datasets in two distinct phases: Map and Reduce.

## The Two Phases
1. **Map:** Distributes chunks of raw data to worker processes/models that filter, extract, and transform each chunk into a structured intermediate ==summary==.
2. **Reduce:** A central aggregator collects all intermediate summaries and synthesizes them into a unified final output. ==summary of summaries==

## Map-Reduce in LLM Context Compression
When analyzing massive document collections (10,000+ personal notes or 200 code repositories) that exceed a single context window:
- **Map:** Fast, cheap models (e.g. Gemini Flash, Claude Haiku) process individual files or repos to output 200-word structured summaries.
- **Reduce:** A deep reasoning model (Gemini Pro, Claude Opus) synthesizes the collection of summaries into a multi-year analysis or cross-repo audit.

The model comes from Google's [2004 paper](https://research.google/pubs/pub62/) by Jeffrey Dean and Sanjay Ghemawat, describing how Google indexed the web. [Hadoop](https://hadoop.apache.org/) is the open-source implementation most people mean when they say "map-reduce" today, and [Spark](https://spark.apache.org/) generalized the idea into a broader dataframe/RDD model that includes map-reduce as one pattern among many, not the only one.

### Related
- [[hierarchical map-reduce note rollup]] — Applying map-reduce to personal Markdown vaults.
- [[multi-repo agentic search architecture]] — Applying map-reduce across multi-repository organizations.
- [[map rollup]] — an OLAP aggregation operation it gets confused with; a different concept, not a synonym.
