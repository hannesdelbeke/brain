---
tags:
  - ai
  - pkm
  - optimization
---
A batch compression pattern for synthesizing thousands of daily notes into monthly and multi-year overviews with minimal LLM API token consumption.

## The Context Window Problem
Feeding 10,000+ raw markdown files directly into frontier LLM context windows burns millions of tokens on repetitive formatting, boilerplate, and low-signal noise.

## The 3-Stage Rollup Pipeline

```
  Daily Notes (Local SQLite / FTS5 Filter)
                     │
                     ▼
  Monthly Summaries (Fast Model: Gemini Flash / Claude Haiku)
                     │
                     ▼
  Multi-Year Meta-Review (Deep Reasoning: Gemini Pro / Claude Opus)
```

1. **Local Pre-Filter:** Strip boilerplate, frontmatter, and non-essential logs using local SQLite metadata indexing (0 token cost).
2. **Daily $\rightarrow$ Monthly Rollup:** Run a fast, lightweight model over pre-filtered daily summaries (~5k tokens per month $\approx$ 60k tokens per year).
3. **Monthly $\rightarrow$ Multi-Year Synthesis:** Send the 12–24 structured monthly summaries to a deep reasoning model for longitudinal psychological, health, or career trajectory analysis (~30k tokens).

Total cost to analyze years of personal logs drops from hundreds of dollars to under $0.20.

### Related
- [[token efficient PKM analysis architecture]] — Overview of vault retrieval and batch analysis economics.
- [[ai overview app]] — High-level application architecture for automated personal overviews.
