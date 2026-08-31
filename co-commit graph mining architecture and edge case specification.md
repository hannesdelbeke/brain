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
When a Git commit touches $N$ files, generating undirected pairs creates $\frac{N(N - 1)}{2}$ edges.
- $N = 2 \implies 1\text{ edge}$
- $N = 5 \implies 10\text{ edges}$
- $N = 20 \implies 190\text{ edges}$
- $N = 500\text{ (bulk refactor / automated linter)} \implies 124,750\text{ edges}$

Naive equal weighting ($w = 1.0$) turns the graph into an unusable hairball. Conversely, hard boolean cutoffs (`if N > 10: drop`) discard authentic multi-document restructuring sessions.

### 2.2 Power-Law Scaling with Floor
Each pairwise edge $(A, B)$ in a commit with $N$ modified files receives weight:

$$w_{\text{size}} = \max\left(w_{\text{floor}},\, \frac{1}{(N - 1)^p}\right)$$

Where:
- $p = 1.5$ (Power-law exponent, heavily prioritizing intimate 2-to-3 file edits).
- $w_{\text{floor}} = 0.005$ (0.5% baseline floor, preserving all large structural edits without graph pollution).
- $N = 2 \implies w = 1.000$
- $N = 3 \implies w = 0.353$
- $N = 5 \implies w = 0.125$
- $N = 20 \implies w = 0.012$ (not yet floored)
- $N \ge 35 \implies w = 0.005$ (floor crossover: solving $1/(N-1)^{1.5} = w_{\text{floor}}$)

---

## 3. Critical Edge Cases & Engineering Solutions

### Edge Case 1: Open-Tab Multi-Tasking & Idle Saves
- **Problem:** Desktop markdown editors (e.g. Obsidian, VS Code) frequently autosave dirty open tabs simultaneously. An idle checklist tab and an active design doc get committed together purely due to timer coincidence.
- **Solution:** 
  - Parse Git diff statistics (`git log --numstat`).
  - Compute modified lines $\Delta L_A$ and $\Delta L_B$.
  - Apply diff volume scaling using geometric mean:
    $$w_{\text{diff}} = \min\left(1.0,\, \frac{\sqrt{\Delta L_A \times \Delta L_B}}{\tau_{\text{lines}}}\right)$$
    where $\tau_{\text{lines}} = 5$ lines. Edits where either file had $<2$ lines modified are aggressively downweighted.

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
    $$\text{Confidence}(A \to B) = \frac{\sum w(A \cap B)}{\sum w(A)}$$
    $$\text{Jaccard}(A, B) = \frac{\sum w(A \cap B)}{\sum w(A) + \sum w(B) - \sum w(A \cap B)}$$
  - When querying related notes for a specific leaf note $A$, its link to a daily log has high confidence ($P(\text{Daily} \mid A) \approx 0.85$). When querying the daily log, individual leaf notes have low confidence ($P(A \mid \text{Daily}) \approx 0.01$), preventing hub noise.

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

### 4.1 Shipped Schema (`co_commit.py`, `~/.pkm/co_commit.db`)

```sql
CREATE TABLE IF NOT EXISTS co_commits (
    vault TEXT NOT NULL,
    note_a TEXT NOT NULL,
    note_b TEXT NOT NULL,
    weight REAL NOT NULL,
    commit_count INTEGER NOT NULL,
    last_commit TEXT NOT NULL,
    last_sha TEXT NOT NULL,
    PRIMARY KEY (vault, note_a, note_b)
);

CREATE INDEX IF NOT EXISTS idx_cc_note_a ON co_commits(vault, note_a);
CREATE INDEX IF NOT EXISTS idx_cc_note_b ON co_commits(vault, note_b);

CREATE TABLE IF NOT EXISTS commit_scan_state (
    vault TEXT PRIMARY KEY,
    last_scanned_sha TEXT NOT NULL,
    scanned_at TEXT NOT NULL
);
```

### 4.2 Proposed Extension (not implemented)

Adding directional confidence and Jaccard (Section 3, Edge Case 3) needs extra columns not in the shipped table today:

```sql
ALTER TABLE co_commits ADD COLUMN jaccard_weight REAL;
ALTER TABLE co_commits ADD COLUMN confidence_ab REAL;
ALTER TABLE co_commits ADD COLUMN confidence_ba REAL;
ALTER TABLE co_commits ADD COLUMN avg_diff_lines REAL;
```

---

## 5. CLI & Retrieval Interface

### 5.1 Shipped (`co_commit.py`: `--db`, `--vault-dir`, `--vault`, `--note`, `--top`, `--rebuild`, `--selfcheck`)

```bash
# 1. Update / Incremental Scan
python co_commit.py --vault root --rebuild

# 2. Query Associations for a Specific Note
python co_commit.py --note "docs/pipeline-architecture.md" --top 10

# 3. Run Self-Check Unit Tests
python co_commit.py --selfcheck
```

### 5.2 Proposed (needs `--metric`, `--direction`, `--min-confidence` — not implemented)

```bash
# Query Directional Outbound Connections, ranked by Jaccard
python co_commit.py --note "docs/pipeline-architecture.md" --direction outbound --metric jaccard --min-confidence 0.2
```

---

## 6. Implementation Checklist for Agents

1. **Extractor Module (`co_commit.py`):**
   - [x] Implement `scan_git_commits` (uses `git log --name-only`, not yet `-M` rename detection or `--numstat`).
   - [x] Implement power-law commit size calculator ($p=1.5, \text{floor}=0.005$) — no Intent multiplier or time decay yet, see Section 2.2.
   - [ ] Implement diff geometric-mean scaling.
2. **Submodule Traversal:**
   - [ ] Recursively walk `.gitmodules` and resolve root-relative canonical paths.
3. **Graph Normalization:**
   - [ ] Compute row-level Jaccard and Confidence scores during post-processing aggregation.
4. **Daemon Integration:**
   - [ ] Expose HTTP endpoint `GET /co_commits?note=<path>&metric=jaccard&limit=10`.
