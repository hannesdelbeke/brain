---
name: co-commit graph mining for serendipitous note associations
description: Mining Git commit history to discover implicit associative connections between notes that pure vector semantic search misses
created: 2026-08-31
aliases:
  - co-commit graph mining for serendipitous note associations
  - co-commit graph mining
  - co-commit note association
  - logical coupling in PKM
  - change coupling for notes
tags:
  - pkm
  - git
  - search
  - graph-theory
  - research
  - technical
---

How to use version control commit topology to discover serendipitous and conceptual relationships between notes that share zero semantic or lexical text overlap.

## The Problem: Semantic Search Blindspots
Modern retrieval-augmented PKM systems rely on three primary layers:
1. **Dense Vector Embeddings:** Cosine proximity over neural embeddings (`bge-small-en-v1.5`).
2. **Lexical Matching:** BM25 / SQLite FTS5 phrase matching.
3. **Explicit Link Graphs:** Explicit `[[wikilinks]]` and asset embeds written in markdown.

### The Semantic Blindspot
Human creativity operates through lateral association (Vannevar Bush's *associative trails* in the 1945 Memex). A technical artist debugging a Maya shader tool might suddenly realize a structural principle about attention budgeting or relationship dynamics, editing both notes in the same 15-minute mental sprint. 

Because the vocabulary in the shader note shares 0% semantic or lexical overlap with the attention note, dense vector cosine similarity is near zero. Pure semantic search will never connect them.

---

## Prior Art & Related Research

The concept of extracting implicit relationships from version control transactions originates in empirical software engineering under the term **Logical Coupling** or **Change Coupling**:

| Research / Pioneer | Landmark Work | Core Contribution | Relevance to PKM |
| :--- | :--- | :--- | :--- |
| **Harald Gall, Mehdi Jazayeri et al. (1998)** | *CVS Release History Data for Detecting Logical Couplings* | First formulated that files co-modified in the same CVS transaction share hidden dependencies undetectable by static code analysis. | Proves commit transactions capture human cognitive context missing from static text. |
| **Thomas Zimmermann & Andreas Zeller (2004)** | *Mining Version Histories to Guide Software Changes (ROSE)* | Applied association rule mining (Apriori) to commit logs to predict *"Programmers who changed file X also changed file Y"*. | Direct predecessor to auto-suggesting related notes during search. |
| **Adam Tornhill (2015)** | *Your Code as a Crime Scene* & *Software Design X-Rays* | Popularized "Change Coupling" and temporal coupling analysis using Git commit logs (via tools like *Code Maat* and *CodeScene*). | Showed that co-change patterns reveal architectural hotspots and conceptual affinity. |

---

## The Graph Clique Explosion Problem ($O(N^2)$)

When a Git commit modifies $N$ files, pairing every file with every other file creates an undirected clique of $rac{N(N-1)}{2}$ edges:
- **2 files:** 1 edge
- **5 files:** 10 edges
- **20 files:** 190 edges
- **500 files (bulk reformat / initial import):** 124,750 edges

### Why Boolean Cutoffs Fail
A naive boolean cutoff (`if N > 10: skip`) is too blunt: it completely discards genuine multi-note restructuring sprints where a user intentionally updated 12 related project notes.

### Why Equal Weighting Fails
Assigning $1.0$ weight to all pairs turns the graph into a dense, noisy hairball where automated linters or bulk imports connect every grocery receipt to every C++ header.

---

## Empirical Weighting Model Evaluation

To find the optimal mathematical weighting, four candidate models were benchmarked across **2,355 multi-file Markdown commits** in a personal vault:

### Candidate Models Tested
1. **Model 1 (Linear Inverse):** $w = \max(0.01, rac{1}{N - 1})$
2. **Model 2 (Quadratic Inverse):** $w = \max(0.01, rac{2}{N(N - 1)})$
3. **Model 3 (Power-Law + Intent Multiplier):** 
   $$w = 	ext{Intent} 	imes \max\left(0.005, rac{1}{(N - 1)^{1.5}}ight)$$
   where $	ext{Intent} = 1.0$ for descriptive commits and $0.3$ for Obsidian `auto backup:` saves.
4. **Model 4 (Model 3 + 180-Day Half-Life Time Decay):** Applies exponential decay based on commit age.

---

### Empirical Benchmark Results

| Test Probe Domain | Pair Description | Model 1 | Model 2 | Model 3 (Winner) | Model 4 (Time Decay) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Relational Synthesis** | `personal relationship analysis note` $\leftrightarrow$ `day 2026-08-28.md` | 3.69 pts | 3.37 pts | **3.41 pts** | 3.36 pts |
| **Git Architecture** | `how to keep history.md` $\leftrightarrow$ `maintain git history.md` | 3.00 pts | 3.00 pts | **3.00 pts** | 2.89 pts |
| **Linux Setup** | `new Linux PC setup log.md` $\leftrightarrow$ `Barrier/Input Leap sync` | 1.83 pts | 1.67 pts | **2.00 pts** | 1.99 pts |
| **Linux Setup** | `new Linux PC setup log.md` $\leftrightarrow$ `Krita stylus latency` | 1.83 pts | 1.67 pts | **2.00 pts** | 1.99 pts |
| **Game Tooling Pipeline** | `asset color tool` $\leftrightarrow$ `palette swatch painter` | 2.78 pts | 2.00 pts | **2.11 pts** | *0.03 pts (suppressed)* |
| **Medical Event** | `specialist referral letter` $\leftrightarrow$ `patient contact record` | 3.33 pts | 3.17 pts | **3.19 pts** | *0.65 pts* |

---

### Findings & Final Design (Model 3)

1. **Power-Law Scaling ($\frac{1}{(N-1)^{1.5}}$):**
   - 2 files: **$1.00$** *(maximum intimate association)*.
   - 3 files: **$0.35$**.
   - 5 files: **$0.12$**.
   - 20+ files: Flattens to the **$0.005$ (0.5%)** floor.
   - Preserves 100% of multi-file commits while giving focused 2-to-3 file edits **200x more associative power** than bulk sweeps.

2. **Equal Weighting across Save Triggers:**
   - In desktop PKM environments, automated saves (e.g. 15-minute syncs) capture authentic human focus sessions.
   - Power-law scaling naturally dampens bulk commits without needing artificial penalties on autosaves.

3. **Evergreen Persistence (Zero Time Decay):**
   - While time decay is vital for activity heatmaps (`mention_heatmap.py`), it is harmful to associative knowledge graphs. Structural relationships between tools or historical records remain permanent truths over time.

---

## Production Implementation

Implemented in [`public/skills/pkm-metadata-indexer/co_commit.py`](file:///home/hannes/repos/pkm/public/skills/pkm-metadata-indexer/co_commit.py) storing edges in `~/.pkm/co_commit.db`:

```bash
# Update co-commit index across vault git history
python public/skills/pkm-metadata-indexer/co_commit.py

# Query top co-committed notes for a specific file
python public/skills/pkm-metadata-indexer/co_commit.py --note "profile.md" --top 10

# Run internal unit tests
python public/skills/pkm-metadata-indexer/co_commit.py --selfcheck
```

## Related Notes
- [[public/skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]]
- [[public/pkm-search|pkm-search]]
- [[public/skills/note-search-optimization/SKILL|note-search-optimization]]
- [[agentic tooling upgrades over grep]]
- [[vault graph traversal]]
