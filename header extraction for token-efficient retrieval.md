---
date: 2026-08-28
created: 2026-08-28
tags:
  - technical
  - pkm
  - retrieval
  - architecture
  - tokens
  - indexing
aliases:
  - header extraction
  - header extraction concept
  - heading extraction
  - structural skeleton retrieval
---

# Header Extraction for Token-Efficient Retrieval

**Header extraction** is the architectural practice of parsing a Markdown document's structural hierarchy (headings `#`, `##`, `###`, line numbers, YAML frontmatter metadata, and lead thesis) into a compact semantic skeleton, rather than loading the entire note body into an LLM context window.

Related: [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[public/pkm-search|pkm-search]], [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]], [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat - modular skills and compact synthesis]]

---

## 1. The Core Problem: Context Bloat in Vault Scanning

When an AI agent searches a Personal Knowledge Management (PKM) vault, it typically evaluates 10 to 50 candidate notes. 

Ingesting full note bodies into the active context window triggers two compounding costs:
1. **Context Window Saturation:** 20 medium-length notes (~1,500 tokens each) consume **30,000 tokens** per turn, pushing context toward early auto-compaction and degrading reasoning quality.
2. **Economic Waste:** The agent usually needs only a single paragraph or sub-point, making 90%+ of the ingested token payload irrelevant.

Header extraction solves this by projecting the document as an **indexable table of contents with line anchors**, allowing the agent to evaluate relevance and execute targeted offset reads (`view_file` with `StartLine`/`EndLine`) only on the required section.

---

## 2. Integration in Vault Indexing Architecture

Recent local-first retrieval infrastructure across the vault implements header-level indexing at the database layer:

* **SQLite Section Slicing ([[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]):** Parses notes into atomic rows in a `sections` table (`path`, `heading`, `start_line`, `end_line`), generating vector embeddings per section rather than averaging the whole note.
* **Retrieval Economics ([[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]):** Shows that line-offset reads cost zero extra API calls because search indices return exact line boundaries.
* **Compact Synthesis ([[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat - modular skills and compact synthesis]]):** Demonstrates how structural outlines prevent instruction dilution.
* **Daemon Query Topology ([[public/pkm-search|pkm-search]] & [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]]):** Answers search queries in milliseconds by returning lightweight section metadata before any raw disk payload is requested.

---

## 3. Concrete Example: [[public/Marion Milner - A Life of One's Own|Marion Milner - A Life of One's Own]]

Consider how [[public/Marion Milner - A Life of One's Own|Marion Milner - A Life of One's Own]] is processed under full ingestion versus header extraction.

### What an AI Sees: Full Note vs. Extracted Header Skeleton

#### Full Note Payload (38 lines, 2,789 characters, ~697 tokens):
The agent receives the entire frontmatter, biographical framing, 5 full explanatory sections, key takeaways, and related wikilinks.

#### Extracted Header Skeleton (11 lines, 559 characters, ~139 tokens):
```yaml
note: Marion Milner - A Life of One's Own
tags: [book-summary, psychology, journaling, attention]
thesis: 7-year diary study investigating happiness; fulfillment emerges from shifting attention from striving to receptive wide sensory awareness.
sections:
  - heading: "1. 'Wide Awareness' over Narrow Attention" (lines 17-23)
  - heading: "2. Spontaneous Delight" (lines 25-27)
  - heading: "3. Detachment from Social Conditioning" (lines 29-31)
  - heading: "4. Unoccupied Solitude and Stillness" (lines 33-35)
  - heading: "5. Reflective Observation through Journaling" (lines 37-39)
  - heading: "Key Takeaway" (lines 41-43)
```

---

## 4. Savings & Performance Comparison

| Metric | Full Note Body | Extracted Skeleton | Reduction / Savings |
|:---|:---|:---|:---|
| **Characters** | 2,789 | 559 | **-79.9%** |
| **Word Count** | 370 words | 77 words | **-79.2%** |
| **Token Payload (est.)** | ~697 tokens | ~139 tokens | **80.0% reduction (5.0x compression)** |
| **Scan Cost (20 Notes)** | ~13,940 tokens | ~2,780 tokens | **11,160 tokens saved per turn** |
| **Scan Cost (50 Notes)** | ~34,850 tokens | ~6,950 tokens | **27,900 tokens saved per turn** |

### Navigational Advantage
If the agent only needs Milner's distinction between striving and sensory awareness, it reads the skeleton (139 tokens), identifies section 1 (`lines 17–23`), and fetches those 7 lines (90 tokens). 

Total tokens consumed: **229 tokens vs. 697 tokens (67.1% net reduction on a single-note retrieval, scaling to 85%+ across multi-note candidate sets)**.
