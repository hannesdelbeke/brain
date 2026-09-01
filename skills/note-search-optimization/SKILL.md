---
name: note-search-optimization
description: Audit, score, and optimize Markdown notes for neural semantic search and token-efficient header extraction.
aliases:
  - note search optimization
  - note-search-optimization
  - search-friendly notes
  - note search readiness
tags:
  - technical
  - pkm
  - skill
  - retrieval
  - search
---

Framework and automated heuristic tooling to optimize Markdown notes for [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], vector embeddings, and [[public/header extraction for token-efficient retrieval|header extraction]].

## Why search-friendly note prep matters

Neural search and header extraction operate on document geometry:
1. **Section Slicing:** Vector search embeds individual sections (`^## `). If a note has no subheadings or vague headings (`## Overview`), embeddings lack topical nuance and agents cannot evaluate relevance from the outline.
2. **Lead Thesis Framing:** First paragraphs carry outsized weight in whole-note summaries and dense document representations. Notes starting with bare code blocks or tables lose semantic grounding.
3. **Link Graph Retrieval:** High-density wikilinks allow 2-hop graph expansion and co-retrieval.

---

## 5 Core Searchability Heuristics

### 1. The "Label : Thesis" Heading Pattern
Replace vague category placeholders (`## Overview`, `## Notes`, `## TODO`, `## Update`) with descriptive claim-bearing headers:
* **Bad:** `## Background`, `## Problem`, `## Solution`
* **Good:** `## Root Cause: Mutex Contention in Search Daemon`, `## Fix: Splitting Query and Index File Locks`
* **Why:** The label anchors visual scanning for humans in Obsidian, while the thesis clause gives agents a zero-read summary directly from the outline skeleton.

### 2. Lead Thesis Statement
Every note must lead with a 1-2 sentence summary explaining the core concept, finding, or claim before introducing code fences, tables, or bullet lists:
* Provides high-density semantic context for top-level search embeddings.
* Allows quick candidate evaluation during outline extraction.

### 3. Frontmatter Aliases & Synonyms
Include frontmatter `aliases` covering acronyms, colloquial phrases, and alternate question phrasings:
```yaml
---
aliases:
  - mutex lock splitting
  - search daemon lock contention
tags:
  - technical
  - architecture
---
```

### 4. Embedding Chunk Sizing
Keep sections between **40 and 350 words**:
* Sections < 30 words produce noisy, low-signal embeddings.
* Sections > 400 words dilute specific concepts and risk embedding truncation. Break large walls of text into distinct `## ` subsections.

### 5. Contextual Wikilinking
Embed wikilinks naturally within explanatory sentences (`she used [[supercharged links]] to decorate DOM nodes`) rather than dumping a list of disconnected links at the bottom.

---

## Automated Heuristic Audit Tool

Use [[audit_search_readiness.py]] to calculate a Searchability Score (0–100) and get actionable refactoring suggestions:

```bash
# 1. Audit entire vault and show lowest-scoring notes:
python public/skills/note-search-optimization/scripts/audit_search_readiness.py --top 10

# 2. Audit a specific folder (e.g. public or work):
python public/skills/note-search-optimization/scripts/audit_search_readiness.py --path "public" --min-score 70

# 3. Audit a single note being created or edited:
python public/skills/note-search-optimization/scripts/audit_search_readiness.py --file "my-note.md"

# 4. Output structured JSON for agent consumption:
python public/skills/note-search-optimization/scripts/audit_search_readiness.py --path "public" --json

# 5. Run test suite:
python public/skills/note-search-optimization/scripts/audit_search_readiness.py --self-check
```

---

## Before & After Refactoring Example

### Before (Unsearchable stub: Score 45/100)
```markdown
# Cache Invalidation
```python
cache.clear()
```
## Notes
- sometimes fails
- need redis
## TODO
- fix this
```

### After (Optimized for Search & Header Extraction: Score 100/100)
```markdown
---
aliases:
  - redis cache invalidation race condition
  - search index cache clear
tags:
  - technical
  - backend
---

In-memory cache invalidation in the search daemon requires distributed locks to prevent stale query reads during background reindexing.

## Root Cause: Race Condition in Concurrent Index Clears
When multiple worker threads trigger `cache.clear()` simultaneously without an atomic lock, in-flight query responses write stale entries back into the cleared cache.

## Resolution: Distributed Mutex via Redis
Wrapping the invalidation pass in a distributed Redis lock guarantees that all workers complete cache flushing before new query reads begin:

```python
with redis_lock("search_cache_invalidation"):
    cache.clear()
```

Related: [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]], [[public/vault hybrid search|vault hybrid search]].
```

---

## Related notes & skills
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]] — SQLite hybrid vector search and link graph engine
- [[public/header extraction for token-efficient retrieval|header extraction for token-efficient retrieval]] — token savings and outline parsing mechanics
- [[public/header extraction|header extraction]] — structural skeleton principles
- [[public/semantic search|semantic search]] — embedding retrieval theory
