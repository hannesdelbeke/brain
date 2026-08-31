---
name: co-commit graph mining architecture and edge case specification
description: Anonymized technical specification and edge-case engineering guide for mining Git co-commit topologies in Personal Knowledge Management systems
created: 2026-08-31
tags:
  - pkm
  - git
  - graph-theory
  - architecture
  - specification
  - technical
aliases:
  - co-commit graph mining architecture and edge case specification
  - co-commit technical specification
  - change coupling for knowledge graphs
---

# Co-Commit Graph Mining for PKM: Technical Specification & Edge Case Engineering

An engineering specification for mining version control history to construct an associative knowledge graph that connects notes across boundaries where dense vector semantic search has zero textual signal.

---

## 1. Problem Statement & Motivation

Modern Personal Knowledge Management (PKM) and retrieval engines rely on dense vector embeddings (e.g. `bge-small-en-v1.5`), lexical token matching (BM25 / SQLite FTS5), and explicit Markdown link graphs (`[[wikilinks]]`).

### The Vector Retrieval Blindspot
Human knowledge synthesis frequently exhibits lateral, cross-domain insights. An engineer building a low-level graphics pipeline tool may simultaneously synthesize a framework for cognitive attention budgeting or organizational management within the same mental sprint. 

Because the vocabulary between these distinct domains shares 0% lexical or semantic overlap, dense cosine similarity is near zero. The implicit cognitive connection is completely invisible to vector search.

However, version control (Git) commits capture exact temporal co-occurrences. Files modified within the same changeset represent an unmined topological knowledge graph.

---

## 2. Core Mathematical Architecture

### 2.1 The Clique Explosion Problem ($O(N^2)$)
When a Git commit touches $N$ files, generating undirected pairs creates $rac{N(N - 1)}{2}$ edges.
- $N = 2 \implies 1	ext{ edge}$
- $N = 5 \implies 10	ext{ edges}$
- $N = 20 \implies 190	ext{ edges}$
- $N = 500	ext{ (bulk refactor / automated linter)} \implies 124,750	ext{ edges}$

Naive equal weighting ($w = 1.0$) turns the graph into an unusable hairball. Conversely, hard boolean cutoffs (`if N > 10: drop`) discard authentic multi-document restructuring sessions.

### 2.2 Power-Law Scaling with Floor
Each pairwise edge $(A, B)$ in a commit with $N$ modified files receives weight:

$$w_{	ext{size}} = \max\left(w_{	ext{floor}},\, rac{1}{(N - 1)^p}ight)$$

Where:
- $p = 1.5$ (Power-law exponent, heavily prioritizing intimate 2-to-3 file edits).
- $w_{	ext{floor}} = 0.005$ (0.5% baseline floor, preserving all large structural edits without graph pollution).
- $N = 2 \implies w = 1.000$
- $N = 3 \implies w = 0.353$
- $N = 5 \implies w = 0.125$
- $N \ge 20 \implies w = 0.005$

---

## 3. Critical Edge Cases & Engineering Solutions

### Edge Case 1: Open-Tab Multi-Tasking & Idle Saves
- **Problem:** Desktop markdown editors (e.g. Obsidian, VS Code) frequently autosave dirty open tabs simultaneously. An idle checklist tab and an active design doc get committed together purely due to timer coincidence.
- **Solution:** 
  - Parse Git diff statistics (`git log --numstat`).
  - Compute modified lines $\Delta L_A$ and $\Delta L_B$.
  - Apply diff volume scaling using geometric mean:
    $$w_{	ext{diff}} = \min\left(1.0,\, rac{\sqrt{\Delta L_A 	imes \Delta L_B}}{	au_{	ext{lines}}}ight)$$
    where $	au_{	ext{lines}} = 5$ lines. Edits where either file had $<2$ lines modified are aggressively downweighted.

### Edge Case 2: Submodule & Multi-Repository Fragmentation
- **Problem:** Knowledge bases organized into Git submodules store commits in separate `.git` trees. A root repository scan only sees 1-line submodule pointer updates, missing all intra-submodule and cross-submodule co-edits.
- **Solution:**
  - Execute recursive commit scanning across all submodule trees (`git submodule foreach`).
  - Normalize submodule-relative paths to root-canonical paths (`submodules/core-docs/architecture.md`).
  - Correlate submodule commits with parent vault commits via commit timestamps within a 5-minute window.

### Edge Case 3: Hub Inflation & Directional Asymmetry
- **Problem:** Central index files (e.g. `daily/YYYY-MM-DD.md`, `README.md`, `INDEX.md`) get committed alongside hundreds of leaf notes. In an undirected graph, hubs dominate all retrieval results.
- **Solution:** 
  - Compute **Directional Association Confidence** and **Jaccard Similarity**:
    $$	ext{Confidence}(A 	o B) = rac{\sum w(A \cap B)}{\sum w(A)}$$
    $$	ext{Jaccard}(A, B) = rac{\sum w(A \cap B)}{\sum w(A) + \sum w(B) - \sum w(A \cap B)}$$
  - When querying related notes for a specific leaf note $A$, its link to a daily log has high confidence ($P(	ext{Daily} \mid A) pprox 0.85$). When querying the daily log, individual leaf notes have low confidence ($P(A \mid 	ext{Daily}) pprox 0.01$), preventing hub noise.

### Edge Case 4: Path Renames & Structural Migrations
- **Problem:** Files are frequently reorganized and renamed. Treating paths as static strings fragments historical edge weights across old and new paths.
- **Solution:**
  - Run Git commit extraction with rename detection (`git log -M -C --name-status`).
  - Maintain an alias/canonical mapping table in SQLite to resolve historical paths to their latest target filename.

### Edge Case 5: Polyglot Inclusion (Code-to-Doc Relationships)
- **Problem:** Filtering exclusively for `.md` files discards the relationship between implementation source code (`src/engine/pipeline.py`) and its architectural design note (`docs/pipeline-spec.md`).
- **Solution:**
  - Include all human-authored source extensions (`.py`, `.ts`, `.js`, `.cpp`, `.h`, `.rs`, `.go`, `.json`, `.sh`).
  - Filter out binary and build artifacts (`.png`, `.exe`, `.dll`, `.wasm`, `.lock`, `.min.js`).

### Edge Case 6: Cross-Repository Temporal Session Correlation
- **Problem:** Developers frequently write code in a standalone project repository (`repo-a`) and, within 15–30 minutes, author or update a companion design document, architectural decision record (ADR), or daily work log in a separate documentation repository (`repo-b`). Because each repository maintains an independent Git DAG, single-repository log extraction misses this cross-repository session link.
- **Solution:**
  - Support a multi-repository registry configuration (`repos.json`).
  - Ingest commit metadata across all registered checkouts onto a single unified global timeline.
  - Apply a **Sliding Temporal Session Window** ($\tau_{\text{session}} \le 30\text{ minutes}$) across commits by the same author:
    $$w_{\text{temporal}} = w_{\text{size}} \times \exp\left(-\frac{\Delta t}{\tau_{\text{session}}}\right)$$
  - Generate cross-repository associative edges between source files in `repo-a` and notes in `repo-b` modified during the active mental sprint.

---

## 4. SQLite Schema Specification

The graph is stored in a standalone SQLite database (`co_commit.db`) or embedded in the main index:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS co_commit_edges (
    corpus TEXT NOT NULL,
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    raw_weight REAL NOT NULL,
    jaccard_weight REAL NOT NULL,
    confidence_ab REAL NOT NULL,
    confidence_ba REAL NOT NULL,
    commit_count INTEGER NOT NULL,
    avg_diff_lines REAL NOT NULL,
    last_commit_date TEXT NOT NULL,
    last_commit_sha TEXT NOT NULL,
    PRIMARY KEY (corpus, source_path, target_path)
);

CREATE INDEX IF NOT EXISTS idx_cce_source ON co_commit_edges(corpus, source_path);
CREATE INDEX IF NOT EXISTS idx_cce_target ON co_commit_edges(corpus, target_path);

CREATE TABLE IF NOT EXISTS commit_scan_state (
    corpus TEXT PRIMARY KEY,
    last_scanned_sha TEXT NOT NULL,
    total_commits_indexed INTEGER NOT NULL,
    scanned_at TEXT NOT NULL
);
```

---

## 5. CLI & Retrieval Interface

```bash
# 1. Update / Incremental Scan
python co_commit.py --corpus root --rebuild

# 2. Query Associations for a Specific Note
python co_commit.py --note "docs/pipeline-architecture.md" --top 10 --metric jaccard

# 3. Query Directional Outbound Connections
python co_commit.py --note "docs/pipeline-architecture.md" --direction outbound --min-confidence 0.2

# 4. Run Self-Check Unit Tests
python co_commit.py --selfcheck
```

---

## 6. Implementation Checklist for Agents

1. **Extractor Module (`co_commit.py`):**
   - [ ] Implement `scan_git_commits` using `git log --name-status --numstat -M`.
   - [ ] Implement power-law commit size calculator ($p=1.5, 	ext{floor}=0.005$).
   - [ ] Implement diff geometric-mean scaling.
2. **Submodule Traversal:**
   - [ ] Recursively walk `.gitmodules` and resolve root-relative canonical paths.
3. **Graph Normalization:**
   - [ ] Compute row-level Jaccard and Confidence scores during post-processing aggregation.
4. **Daemon Integration:**
   - [ ] Expose HTTP endpoint `GET /co_commits?note=<path>&metric=jaccard&limit=10`.
