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
  - assertion headers
---

# Header Extraction for Token-Efficient Retrieval

**Header extraction** is the architectural practice of parsing a [[Markdown]] document's structural hierarchy (headings `#`, `##`, `###`, line numbers, YAML frontmatter metadata, and lead thesis) into a compact semantic skeleton, rather than loading the entire note body into an [[AI agent|agent's]] active context window.

Related: [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]], [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[public/pkm-search|pkm-search]], [[public/token efficient PKM analysis architecture|token efficient PKM analysis architecture]], [[public/pkm vault indexing landscape|pkm vault indexing landscape]], [[public/vault hybrid search|vault hybrid search]], [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]], [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat - modular skills and compact synthesis]]

---

## 1. The Core Problem: Context Bloat in Vault Scanning

When an [[AI agent]] searches a [[personal knowledge management|Personal Knowledge Management (PKM)]] vault for [[retrieval augmented generation|retrieval augmented generation (RAG)]], it typically evaluates 10 to 50 candidate notes. 

Ingesting full note bodies into the active context window triggers two compounding costs:
1. **Context Window Saturation:** 20 medium-length notes (~1,500 [[AI tokens|tokens]] each) consume **30,000 tokens** per turn, pushing context toward early auto-compaction and degrading reasoning quality.
2. **Economic Waste:** The agent usually needs only a single paragraph or sub-point, making 90%+ of the ingested token payload irrelevant.

Header extraction solves this by projecting the document as an **indexable table of contents with line anchors**, allowing the agent to evaluate relevance and execute targeted offset reads (`view_file` with `StartLine`/`EndLine`) only on the required section.

---

## 2. Integration in Vault Indexing Architecture

Recent local-first retrieval infrastructure across the [[personal knowledge management|PKM]] vault implements header-level indexing at the database layer:

* **SQLite Section Slicing ([[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]):** Parses [[Markdown]] notes into atomic rows in a `sections` table (`path`, `heading`, `start_line`, `end_line`), generating [[vector embedding|vector embeddings]] per section rather than averaging the whole note.
* **Retrieval Economics ([[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]):** Shows that line-offset reads cost zero extra API calls because search indices return exact line boundaries.
* **Compact Synthesis ([[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat - modular skills and compact synthesis]]):** Demonstrates how structural outlines prevent instruction dilution in multi-agent workflows.
* **Daemon Query Topology ([[public/pkm-search|pkm-search]] & [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]]):** Answers search queries in milliseconds by returning lightweight section metadata before any raw disk payload is requested.

---

## 3. Case Study: Header Evolution on [[public/Marion Milner - A Life of One's Own|Marion Milner - A Life of One's Own]]

The retrieval value of an extracted outline depends directly on **heading design**. Comparing the three iterations of [[public/Marion Milner - A Life of One's Own|Marion Milner - A Life of One's Own]] illustrates the progression from passive topics to clumsy sentences, and finally to the optimal human-AI hybrid format.

### Version 0: Raw Generic Topic Labels (Original Web Scrape)
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
* **Pros:** Fast for human skimming in [[Obsidian]].
* **Failure Mode:** Zero information density for AI. The agent sees categories (*"Overview"*, *"Creative Practices"*), but cannot know the causal claims without reading the entire body.

---

### Version 1: Full-Sentence Assertion Headers (High AI Density, Low Human Scannability)
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
* **Pros:** High semantic value for AI; completely answers questions without reading body text.
* **Cons (Human UX):** Wordy, clumsy in [[Obsidian]] outline sidebars, wraps awkwardly on smaller screens, and slows down visual scanning for humans.

---

### Version 2: The "Label : Core Thesis" Hybrid Pattern (The Optimal Solution)
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
  1. **Human Visual Scannability:** The eye instantly anchors on the bold category label (*Wide Awareness*, *Social Pressure*, *Solitude*) in [[Obsidian]].
  2. **AI Zero-Read Completeness:** The sub-clause after the colon supplies the exact causal mechanism (*"Releasing Approval, Prestige, and Productivity"*).
  3. **High-Signal Vector Embeddings:** [[vector embedding|Semantic vector search]] over the heading matches nuanced user queries without dilution.

---

## 4. Architectural Comparison Across Header Paradigms

| Attribute | Generic Topic Labels (V0) | Full Sentences (V1) | Hybrid "Label : Thesis" (V2) |
|:---|:---|:---|:---|
| **Human Scannability** | High (punchy, clean) | Low (wordy, wraps in TOC) | **High (anchored prefix)** |
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

### Summary
By adopting the **"Label : Core Thesis" hybrid pattern**, [[personal knowledge management|PKM]] notes maintain human elegance and visual clarity in [[Obsidian]] while simultaneously serving as high-density, zero-read semantic outlines for [[AI agent|AI agents]].
