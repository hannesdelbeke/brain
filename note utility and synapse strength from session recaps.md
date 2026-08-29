---
aliases:
  - post-session note utility scoring
  - credit assignment for note utility
  - outcome-driven synapse weighting
  - agent usefulness view count
  - session recap note utility
tags:
  - pkm
  - ai
  - search
  - graph-theory
  - architecture
---

Agent execution sessions provide the missing ground-truth feedback loop for note usefulness. By comparing the starting prompt, notes read during the turn, the session recap, and the resulting git commit, an evaluator assigns credit to notes that drove successful outcomes. This replaces naive view counts with real task utility scores and strengthens associative synaptic edges in SQLite.

## Why raw view counts and passive retrieval fall short

Obsidian [[view count]] measures human navigation clicks, missing agent reads entirely.

Passive co-retrieval logging in [[2026-08-27 every read is a write - co-retrieval as synapse strength|every read is a write]] captures what the daemon returned, but builds a rich-get-richer loop: a note ranked high gets retrieved often, yet retrieval alone doesn't prove it helped solve the user's task.

## The session feedback loop

Every productive agent run contains three reliable anchors:
- Human prompt: the initial intent, problem description, and constraints (see [[track prompt history]]).
- Read trace: the list of note paths fetched via `searchd` or opened via tool calls during the run.
- Outcome: the final git commit diff representing the working solution, paired with the agent session recap.

At session end or during nightly consolidation ([[grow memory]]), a lightweight evaluator evaluates credit assignment: did a read note supply the core logic, pattern, constraint, or syntax that enabled the git commit?

```
┌────────────────────────────────────────────────────────┐
│                   AGENT SESSION                        │
│   Prompt ──▶ Query searchd / Read Notes ──▶ Commit     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│         POST-SESSION CREDIT EVALUATION                 │
│  Compare Prompt + Read Notes + Recap vs Git Diff       │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
┌─────────────────────────┐ ┌────────────────────────────┐
│   Note Utility Score    │ │   Hebbian Synaptic Edges   │
│ (agent viewcount for    │ │ (co-utilized notes get     │
│  proven task leverage)  │ │  strengthened in SQLite)   │
└─────────────────────────┘ └────────────────────────────┘
```

## Dual outputs: utility scores and Hebbian synapses

### 1. Note utility score (agent usefulness view count)
Each note accumulates a verified utility score in the index database. A note cited or applied in a successful commit receives positive reinforcement (+3), a read note that was irrelevant gets neutral (+0.1), and notes retrieved during broken or reverted turns get penalized (-1).

This score acts as an agent-aware view count. High-utility notes get boosted in hybrid search rankings, while notes with high retrieval counts but zero utility are flagged for [[vault synapse pruning]].

### 2. Hebbian co-utility synapses
Notes that jointly contribute to solving the same prompt gain edge weight ($A \leftrightarrow B$) in the index `edges` table. 

Unlike static text similarity, co-utility reflects functional synergy discovered through real problem solving. When co-utility weight crosses a threshold over multiple sessions, it suggests candidate explicit wikilinks across previously unlinked notes.

## Storage boundaries: keep telemetry in SQLite

Utility scores and synaptic weights belong in SQLite (`pkm_index.db`), never in note [[YAML front matter]].

Writing scores directly into note markdown causes immediate failure modes:
- Pollutes git history with automated score churn.
- Overwrites file modification timestamps, breaking recently edited lists.
- Triggers continuous file watcher loops and backup stalls (see [[view count]]).

## Related notes
- [[2026-08-27 every read is a write - co-retrieval as synapse strength]] — retrieval-time logging that this post-session pass validates
- [[hosted PKM vector index and note utility]] — utility telemetry model and score deltas
- [[view count]] — human view tracking vs agent utility metrics
- [[track prompt history]] — capturing prompt intent in git commits
- [[cross-agent session indexing architecture]] — indexing session transcripts and tool calls
- [[vault synapse pruning]] — using utility signals to prune dead links and outdated notes
- [[2026-08-27 synapse links vs wikilinks and semantic links]] — comparing dynamic synaptic edges to static wikilinks
- [[grow memory]] — nightly consolidation pass where credit assignment runs
