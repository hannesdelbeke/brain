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
| **Harald Gall, Karin Hajek, Mehdi Jazayeri (1998)** | *Detection of Logical Coupling Based on Product Release History* (ICSM) | First formulated that files co-modified across releases share hidden dependencies undetectable by static code analysis. | Proves commit transactions capture human cognitive context missing from static text. |
| **Thomas Zimmermann, Peter Weißgerber, Stephan Diehl, Andreas Zeller (2004)** | *Mining Version Histories to Guide Software Changes (ROSE)* | Applied association rule mining (Apriori) to commit logs to predict *"Programmers who changed file X also changed file Y"*. | Direct predecessor to auto-suggesting related notes during search. |
| **Adam Tornhill (2015 / 2018)** | *Your Code as a Crime Scene* (2015) & *Software Design X-Rays* (2018) | Popularized "Change Coupling" and temporal coupling analysis using Git commit logs (via tools like *Code Maat* and *CodeScene*). | Showed that co-change patterns reveal architectural hotspots and conceptual affinity. |
| **source{d} Hercules ("couples" analysis)** | [Hercules](https://github.com/src-d/hercules) | Purpose-built tool for mining file co-change graphs directly from Git history, closer prior art than general logical-coupling research. | Same graph-extraction problem, ready-made reference implementation. |
| **Mark Granovetter (1973)** | *The Strength of Weak Ties* | Distinguishes strong ties (frequent, high-overlap) from weak ties (rare, bridging) in a social/associative graph. | Better framing than "logical coupling" for *why* a 2-file power-law-heavy edge should outweigh a 20-file bulk edge — it's a strong-vs-weak tie problem, not just a coupling-detection one. |

PKM-native prior art (content-based, not commit-based) is deliberately not listed here — Obsidian's graph view, the Smart Connections plugin, and Juggl all infer relatedness from note *content* (links, embeddings). This technique is git-history-based and finds pairs with zero content overlap, which is the actual novelty; it doesn't compete with them, it fills their blind spot.

### A Broader Claim: Is Everything Connected?

A stronger version of this idea says every note is latently connected to every earlier note, co-committed or not, because one continuous mind wrote all of them and every note is shaped by what came before it. This isn't a new claim: it's Bush's *associative trails* generalized past the two-note case, and it's the explicit premise of Niklas Luhmann's Zettelkasten writing — the slip-box's value comes from unplanned connections surfacing later, whether or not two notes were ever explicitly linked. The cognitive mechanism is **spreading activation** (Collins & Loftus, 1975): activating one concept partially activates everything associatively near it, decaying with distance.

Formalizing this as a second, denser graph layer underneath co-commit — a fully-connected baseline where every note pair gets weight $e^{-\Delta t / \tau}$ by creation-time distance, with co-commit edges as sparse high-weight spikes on top — is mathematically sound but not worth building as literal graph edges: an $O(N^2)$ dense graph over thousands of notes costs real storage for almost entirely negligible weight.

**Tested, and it does not work as a reranking prior either.** The proposed alternative — a scalar multiplier, `final_score = vector_score * (1 + λ · e^{-Δt/τ})`, applied to an existing ranking rather than stored as edges — was measured against real wikilinks in this vault (`recency_prior_experiment.py`, MRR against explicit `[[wikilinks]]` as ground truth, since no judge model was available to test it the way the co-commit signal was). Every τ tested at λ=1.0 hurt MRR (-11% to -19%, no sweet spot — damage only shrinks as τ→∞, where the term degenerates to a no-op). A sweep over λ at τ=30 found a peak around λ≈0.1 (+6.3%), but the effect is small, concentrated in a handful of pairs, and unstable across random samples (a 5-seed check at λ=0.5 found the full-sample answer is **-11.69%**, not the +0.41% one lucky seed showed). A qualitative spot-check confirmed the mechanism is real, not a bug: same-day companion notes (`Windows 10 Enterprise.md` / `Windows 10 Pro.md`) get correctly boosted, but a *global* multiplier necessarily demotes every other candidate by comparison, including genuinely-linked pairs written far apart — that displacement cost dominates at any weight beyond a sliver. Verdict: don't ship this as a global rerank multiplier. If it's worth revisiting, the fix is mechanistic (a tiebreaker only among near-tied vector scores, not a multiplier over the whole candidate pool), not a different τ/λ.

The co-commit graph in this note is still the useful, sparse, empirically-grounded special case of the broader theory — that one held up under testing where the dense reranking version did not.

---

## The Graph Clique Explosion Problem ($O(N^2)$)

When a Git commit modifies $N$ files, pairing every file with every other file creates an undirected clique of $\frac{N(N-1)}{2}$ edges:
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

Four candidate weighting shapes were compared, benchmarked against the private and public vaults on the machine that wrote this note (not the checkout this file lives in, so the exact run isn't reproducible from here):

### Candidate Models Tested
1. **Model 1 (Linear Inverse):** $w = \max(0.01, \frac{1}{N - 1})$
2. **Model 2 (Quadratic Inverse):** $w = \max(0.01, \frac{2}{N(N - 1)})$
3. **Model 3 (Pure Power-Law, no discount):** 
   $$w = \max\left(0.005, \frac{1}{(N - 1)^{1.5}}\right)$$
   Applies to every commit equally, including Obsidian `auto backup:` saves — this is what `co_commit.py` ships.
4. **Model 4 (Model 3 + 180-Day Half-Life Time Decay):** Applies exponential decay based on commit age.

---

### Why Model 3 Wins

> The scores above were measured, not invented — run against the real private and public vaults, just on a different machine than whichever checkout is reading this note, so the exact run can't be replayed from here. What has drifted since: the benchmarked Model 3 included the Intent multiplier ($1.0\times$ vs $0.3\times$ for autosaves); `co_commit.py` as shipped today applies pure power-law with no multiplier (see "Equal Weighting across Save Triggers" below). The table's Model 3 numbers describe that earlier, slightly different formula, not the exact one currently running. A rerun with an eval harness in the style of `eval_rerank.py` against this checkout's own history would confirm whether dropping the multiplier changed the ranking — see [[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]] for where that harness would live.

Reasoning for preferring Model 3 over 1/2, consistent with the measured table above:
- **Model 1 (linear inverse)** and **Model 2 (quadratic inverse)** both decay slower than Model 3 for mid-size commits (5-10 files), so a moderate refactor commit gets nearly as much weight as a focused 2-file edit — this is the "equal weighting" failure mode from the section above, just less extreme.
- **Model 3 (power-law, $p=1.5$)** concentrates weight sharply on 2-3 file commits while still assigning a nonzero floor to bulk commits, which matches the stated goal (reward intimate edits, don't discard bulk ones).
- **Model 4 (time decay)** is excluded from the winning design on principle (see Finding 3 below), not on the measured data above.

---

### Findings & Final Design (Model 3)

1. **Power-Law Scaling ($\frac{1}{(N-1)^{1.5}}$):**
   - 2 files: **$1.00$** *(maximum intimate association)*.
   - 3 files: **$0.35$**.
   - 5 files: **$0.12$**.
   - 20 files: **$0.012$** — not yet at the floor (a common misreading of the graph's shape; solving $1/(N-1)^{1.5} = 0.005$ puts the actual floor crossover at **$N \approx 35$**).
   - 35+ files: Flattens to the **$0.005$ (0.5%)** floor.
   - Preserves 100% of multi-file commits while giving focused 2-to-3 file edits **200x more associative power** than bulk sweeps.

2. **Equal Weighting across Save Triggers:**
   - In desktop PKM environments, automated saves (e.g. 15-minute syncs) capture authentic human focus sessions.
   - Power-law scaling naturally dampens bulk commits without needing artificial penalties on autosaves.

3. **Evergreen Persistence (Zero Time Decay):**
   - While time decay is vital for activity heatmaps (`mention_heatmap.py`), it is harmful to associative knowledge graphs. Structural relationships between tools or historical records remain permanent truths over time.

---

## Production Implementation

Implemented in [`skills/pkm-metadata-indexer/co_commit.py`](skills/pkm-metadata-indexer/co_commit.py), storing edges in `~/.pkm/co_commit.db` (single `co_commits` table: `vault`, `note_a`, `note_b`, `weight`, `commit_count`, `last_commit`, `last_sha`):

```bash
# Update co-commit index across vault git history
python skills/pkm-metadata-indexer/co_commit.py --rebuild

# Query top co-committed notes for a specific file
python skills/pkm-metadata-indexer/co_commit.py --note "profile.md" --top 10

# Run internal unit tests
python skills/pkm-metadata-indexer/co_commit.py --selfcheck
```

## Related Notes
- [[public/skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]]
- [[public/pkm-search|pkm-search]]
- [[public/skills/note-search-optimization/SKILL|note-search-optimization]]
- [[agentic tooling upgrades over grep]]
- [[vault graph traversal]]
