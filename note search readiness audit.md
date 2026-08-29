---
created: 2026-08-30
tags:
- technical
- pkm
- retrieval
- search
- indexing
- audit
aliases:
- vault search readiness audit
- note search optimization audit 2026-08
- note searchability benchmark
---

Audit findings across 3,830 evergreen and technical notes evaluated with [[public/skills/note-search-optimization/SKILL|note search optimization]] heuristics for [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]] and [[public/header extraction for token-efficient retrieval|header extraction]].

Excluded chronological daily logs, raw transcript dumps, and archives to focus exclusively on reusable knowledge.

## Vault score distribution

| Tier | Notes | Percentage | Status |
| :--- | :--- | :--- | :--- |
| 🟢 **Excellent (90–100)** | **1,837** | **48.0%** | Optimal for neural vector search and outline extraction |
| 🟡 **Good (75–89)** | **1,647** | **43.0%** | Searchable; minor gaps in aliases or link density |
| 🟠 **Needs Structure (50–74)** | **322** | **8.4%** | Missing lead thesis, untyped code, or un-chunked sections |
| 🔴 **Low Searchability (<50)** | **8** | **0.2%** | Bare tables/code dumps without headers or prose |

Overall average searchability score across relevant notes: **87.8 / 100**.

## Top 5 searchability bottlenecks

### 1. Missing frontmatter aliases (88.5% / 3,389 notes)
Most notes declare `tags` and `sentiment`, but lack `aliases`.
- *Impact:* Queries using synonyms, acronyms, or colloquial phrasing miss lexical exact-match anchors.
- *Remedy:* Add frontmatter `aliases` for alternate names and acronyms.

### 2. Missing or brief lead thesis (31.1% / 1,190 notes)
Notes opening directly into a list, table, code block, or subheader without an introductory claim sentence (< 8 words).
- *Impact:* Whole-note vector embeddings lack core framing and topical context.
- *Remedy:* Lead with 1–2 complete sentences framing the finding or concept before data blocks.

### 3. Orphan notes & low link density (14.7% / 565 notes)
Notes with 0 or only 1 outbound wikilink disconnected from the vault link graph.
- *Impact:* Ineffective 2-hop graph expansion and co-retrieval.
- *Remedy:* Embed contextual wikilinks into explanatory sentences.

### 4. Untyped code fences (7.5% / 286 notes)
Bare code fences (` ``` `) missing language tags (`python`, `bash`, `sql`, `json`).
- *Impact:* Decreased parsing accuracy during language-filtered code block retrieval.
- *Remedy:* Explicitly declare syntax identifiers on all code blocks.

### 5. Un-chunked walls of text (3.1% / 118 notes)
Long notes (> 400 words) with no `## ` section headings.
- *Impact:* Header extraction cannot slice specific subsections, forcing full-body token ingestion.
- *Remedy:* Break text into "Label : Thesis" subsections (40–350 words per chunk).

## High-impact refactoring clusters

The lowest-scoring notes cluster into three distinct structural patterns:

- **Bare script dumps:** Standalone code files with no explanatory prose. Fix by adding a 1-sentence lead explaining what the script accomplishes, declaring code languages, and adding aliases.
- **Naked data tables:** Standalone benchmark or financial logs. Fix by adding a short summary above the table describing key takeaways.
- **Long un-chunked reference notes:** Extensive legacy guides without `## ` headers. Fix by chunking into 3–4 informative sections (`## Core Utility: ...`, `## Setup: ...`).

## Related notes
- [[public/skills/note-search-optimization/SKILL|note search optimization]] — audit heuristics and automated scoring CLI
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]] — SQLite hybrid vector search and link graph engine
- [[public/header extraction for token-efficient retrieval|header extraction for token-efficient retrieval]] — token savings from outline slicing
- [[public/header extraction|header extraction]] — document outline extraction principles
- [[public/token efficient PKM analysis architecture|token efficient PKM analysis architecture]] — low-cost scanning strategies
