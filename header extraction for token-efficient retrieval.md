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
  - header extraction for token-efficient retrieval
  - token-efficient header retrieval
  - assertion headers retrieval
---

# Header Extraction for Token-Efficient Retrieval

Using [[header extraction]] allows an [[AI agent]] scanning a [[personal knowledge management|PKM]] vault for [[retrieval augmented generation]] to evaluate document topology via structural skeletons, avoiding the token cost of ingesting full note bodies.

Related: [[header extraction]], [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[public/pkm-search|pkm-search]], [[public/token efficient PKM analysis architecture|token efficient PKM analysis architecture]], [[public/vault hybrid search|vault hybrid search]], [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]], [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat - modular skills and compact synthesis]]

---

## 1. Context Bloat in Candidate Scanning

When an [[AI agent]] searches a vault, candidate pools range from 10 to 50 notes. 

* **Full Body Ingestion:** 20 medium notes (~1,500 [[AI tokens|tokens]] each) consume **30,000 tokens** per turn, rapidly filling the context window and triggering early compaction.
* **Header Extraction Alternative:** Extracting the [[header extraction|structural skeleton]] projects each document as an indexable outline with line anchors. The agent evaluates relevance on the outline and fetches only the required line range via offset reads (`view_file` with `StartLine`/`EndLine`).

---

## 2. Integration in Vault Indexing Architecture

* **Section Slicing ([[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]):** Implements [[chunking]] at heading boundaries, storing atomic rows in SQLite (`path`, `heading`, `start_line`, `end_line`) with [[vector embedding|vector embeddings]] per section.
* **Zero-Cost Offset Slicing ([[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]):** Line-offset reads cost zero extra API calls because search indices return exact line boundaries.
* **Pre-Payload Querying ([[public/pkm-search|pkm-search]]):** Answers queries by returning lightweight section metadata before loading raw text from disk.

---

## 3. Case Study: Header Evolution on [[public/Marion Milner - A Life of One's Own|Marion Milner - A Life of One's Own]]

The retrieval efficiency of an extracted outline depends on heading design. Comparing three iterations on [[public/Marion Milner - A Life of One's Own|Marion Milner - A Life of One's Own]]:

### Version 0: Generic Topic Labels (Original Web Scrape)
```yaml
sections:
  - "Overview"
  - "Key Sources of Happiness She Identified"
  - "1. Wide Awareness — Deep, Sensory Attention"
  - "2. Spontaneous Moments of Delight"
  - "3. Freedom from Social Pressures"
  - "4. Inner Stillness and Solitude"
  - "5. Creative and Reflective Practices"
  - "Her Overall Conclusion"
```
* **Failure Mode:** Zero information density for an [[AI agent]]. Headings are passive category buckets; the agent cannot determine claims without reading the entire body.

---

### Version 1: Full-Sentence Assertion Headers
```yaml
sections:
  - "Core Findings: The 7-Year Diary Study on Spontaneous Happiness" (lines 19-20)
  - "1. Wide Panoramic Awareness vs. Narrow Task-Driven Focus" (lines 21-27)
  - "2. Fleeting Spontaneous Micro-Delight over Planned Milestones" (lines 28-30)
  - "3. Detachment from Social Approval, Prestige, and Productivity Pressure" (lines 31-33)
  - "4. Unoccupied Solitude and Non-Doing as Space for Authentic Desires" (lines 34-36)
  - "5. Journaling and Free Drawing as Active Self-Clarification Instruments" (lines 37-39)
  - "Central Takeaway: Happiness Emerges from Receptive Attention, Not Achievement" (lines 40-42)
```
* **Failure Mode:** High semantic value for AI, but visually cluttered in [[Obsidian]] outline panes and difficult for human visual scanning.

---

### Version 2: The "Label : Core Thesis" Hybrid Pattern
```yaml
note: Marion Milner - A Life of One's Own
tags: [book-summary, psychology, journaling, attention]
thesis: 7-year diary study investigating happiness; fulfillment emerges from shifting attention from striving to receptive wide sensory awareness.
sections:
  - heading: "Core Findings: 7-Year Happiness Diary Study" (lines 19-20)
  - heading: "1. Wide Awareness: Panoramic Sensory Perception over Goal-Striving" (lines 21-27)
  - heading: "2. Spontaneous Delight: Fleeting Micro-Moments over Planned Milestones" (lines 28-30)
  - heading: "3. Social Pressure: Releasing Approval, Prestige, and Productivity" (lines 31-33)
  - heading: "4. Solitude: Unoccupied Non-Doing as Space for Authentic Desires" (lines 34-36)
  - heading: "5. Journaling: Reflective Writing and Drawing as Self-Clarification" (lines 37-39)
  - heading: "Key Takeaway: Receptive Attention over Achievement" (lines 40-42)
```
* **Why V2 Wins:**
  1. **Human Visual Scannability:** The bold category label front-loads the keyword for fast visual navigation in [[Obsidian]].
  2. **AI Zero-Read Completeness:** The clause after the colon provides the complete causal mechanism directly to the [[AI agent]].
  3. **High-Signal Embeddings:** Generates targeted [[vector embedding|vector embeddings]] for nuanced search queries.

---

## 4. Architectural Comparison Across Header Paradigms

| Attribute | Generic Topic Labels (V0) | Full Sentences (V1) | Hybrid "Label : Thesis" (V2) |
|:---|:---|:---|:---|
| **Human Scannability** | High (clean) | Low (wordy, wraps in TOC) | **High (anchored prefix)** |
| **AI Zero-Read Capability** | 0% (must read body) | 100% (complete thesis) | **100% (complete thesis)** |
| **Vector Match Accuracy** | Low (weak cosine similarity) | High (nuanced matching) | **High (targeted matching)** |
| **Visual Friction in Obsidian** | Minimal | High visual clutter | **Clean & structured in [[Obsidian]]** |
| **Token Payload (Outline)** | ~50 [[AI tokens|tokens]] | ~85 [[AI tokens|tokens]] | **~75 [[AI tokens|tokens]]** |

---

## 5. Token & Savings Breakdown

| Metric | Full Note Body | Extracted V2 Outline | Net Savings |
|:---|:---|:---|:---|
| **Characters** | 2,750 | 620 | **-77.5%** |
| **Word Count** | 365 words | 82 words | **-77.5%** |
| **Token Payload (est.)** | ~688 [[AI tokens|tokens]] | ~155 [[AI tokens|tokens]] | **77.5% reduction (4.4x compression)** |
| **Scan Cost (20 Notes)** | ~13,760 tokens | ~3,100 tokens | **10,660 tokens saved per turn** |
| **Scan Cost (50 Notes)** | ~34,400 tokens | ~7,750 tokens | **26,650 tokens saved per turn** |
