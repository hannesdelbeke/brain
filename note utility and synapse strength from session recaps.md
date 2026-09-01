---
aliases:
  - post-session note utility scoring
  - credit assignment for note utility
  - outcome-driven synapse weighting
  - agent usefulness view count
  - session recap note utility
  - causal note credit assignment
tags:
  - pkm
  - ai
  - search
  - graph-theory
  - architecture
---

Agent execution sessions provide the missing ground-truth feedback loop for note usefulness. By comparing the starting prompt, notes read during the turn, the session recap, and the resulting git commit diff, an evaluator assigns causal credit to notes that drove successful outcomes. This replaces naive view counts with real task utility scores and strengthens associative synaptic edges in SQLite without touching note markdown.

## Why raw view counts and passive retrieval fall short

Obsidian [[view count]] tracks human navigation waypoints and active topic hubs. It records file opens, but misses all agent reads and cannot measure whether a note contained the core solution or was merely a navigational waypoint.

Passive co-retrieval logging in [[2026-08-27 every read is a write - co-retrieval as synapse strength|every read is a write]] captures queries and returned candidates in [[searchd.py]]. While valuable for tracking query impressions, ranking solely on raw retrievals creates a **rich-get-richer loop**: notes ranked highly by initial BM25/vector embeddings get retrieved repeatedly, accumulating weight regardless of whether they helped or acted as noisy distractors.

True usefulness requires measuring **task resolution**: did reading a note directly contribute to the working code, decision, or synthesis committed at the end of the turn?

## The session feedback loop (causal credit assignment)

Every productive agent execution turn provides four concrete anchors:
- **Prompt:** User intent, constraints, and problem statement (recorded in git commit body per [[track prompt history]]).
- **Read trace:** Note paths fetched from [[searchd.py]] or inspected via tool calls (`view_file`, `grep_search`).
- **Session recap:** The agent's final synthesized explanation of how the problem was resolved.
- **Git commit diff:** The ground-truth outcome—the exact code, configuration, or note changes verified as working.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AGENT RUNTIME SESSION                           │
│   Prompt ──▶ searchd query ──▶ Read Notes [A, B, C] ──▶ Git Commit + Recap
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   POST-SESSION CREDIT ASSIGNMENT                       │
│  Compare Prompt + Read Notes + Recap against Git Commit Diff           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
             ┌──────────────────────┴──────────────────────┐
             ▼                                             ▼
┌──────────────────────────────┐              ┌──────────────────────────┐
│      Note Utility Score      │              │  Hebbian Co-Utility Edge │
│  (agent-aware usefulness     │              │  (strengthens A ↔ B for  │
│   score in pkm_index.db)     │              │   shared task resolution)│
└──────────────────────────────┘              └──────────────────────────┘
```

## Credit assignment heuristics

Evaluating note usefulness can run cheaply through deterministic heuristics or through an asynchronous LLM evaluation pass during nightly consolidation ([[grow memory]]).

### 1. Deterministic heuristics (zero LLM token cost)
- **Diff symbol overlap:** The git commit diff introduces or modifies functions, variables, architecture names, or frontmatter tags uniquely defined in Note A.
- **Recap citation & synthesis:** The agent's final recap or tool thoughts explicitly cite Note A as the source for the chosen strategy.
- **Turn proximity:** Note A was read within 1–2 turns immediately preceding the file edit tool call.
- **Edit derivative:** Note A itself was modified, refined, or had derivative notes spawned from its contents.

### 2. Utility scoring model
Each note accumulates an impression-normalized utility score in `pkm_index.db`:

- **Primary causal driver (+3.0):** Note supplied the essential pattern, code snippet, or constraint used in the git commit.
- **Supporting context (+1.0):** Note provided necessary background or verified what not to do.
- **Neutral retrieval (+0.1):** Note returned in search results or opened briefly without contributing to the outcome.
- **Distractor / penalty (-1.0):** Note read during failed execution paths, aborted tool calls, or runs requiring human correction.

To prevent high-impression hub notes from dominating, score normalization divides cumulative reward by total impressions:

$$U(n) = \frac{\sum_{s \in S} \text{Reward}(n, s)}{\text{Impressions}(n)^\alpha}$$

where $\alpha \in [0.5, 0.8]$ acts as an impression dampener. A note opened 5 times with 4 positive outcomes ranks significantly higher than a note returned 300 times that only proved useful twice.

## Hebbian co-utility synaptic graph

When multiple notes (e.g. Note A and Note B) both receive positive credit in the same session for solving prompt P, their mutual edge in the `edges` table is strengthened:

$$\Delta W_{AB} = \eta \cdot \text{Reward}(A, s) \cdot \text{Reward}(B, s)$$

This implements biological Long-Term Potentiation (LTP) based on **functional co-utilization** rather than superficial lexical overlap. Over time:
- Notes that solve complementary halves of a problem (e.g. a database schema note and an API endpoint note) develop strong synaptic bonds.
- Dynamic graph traversal in [[vault graph traversal]] uses these edges to expand search context across folder boundaries.
- Edges that cross a sustained strength threshold over 30 days can be auto-suggested as explicit `[[wikilinks]]`.

## Database schema

All utility telemetry lives in SQLite (`pkm_index.db`), completely separated from Markdown files.

```sql
-- Per-note utility aggregates
CREATE TABLE note_utility (
    note_id         INTEGER PRIMARY KEY,
    total_reads     INTEGER NOT NULL DEFAULT 0,
    useful_reads    INTEGER NOT NULL DEFAULT 0,
    impressions     INTEGER NOT NULL DEFAULT 0,
    utility_score   REAL NOT NULL DEFAULT 0.0,
    last_useful_at  TEXT,
    FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
);

-- Session-level credit logs
CREATE TABLE session_credit (
    session_id      TEXT NOT NULL,
    note_id         INTEGER NOT NULL,
    reward          REAL NOT NULL,
    heuristic_flags TEXT,
    created_at      TEXT NOT NULL,
    PRIMARY KEY (session_id, note_id)
);

-- Synaptic co-utility edges
CREATE TABLE co_utility_edges (
    source_id       INTEGER NOT NULL,
    target_id       INTEGER NOT NULL,
    co_activations  INTEGER NOT NULL DEFAULT 0,
    weight          REAL NOT NULL DEFAULT 0.0,
    last_reinforced TEXT NOT NULL,
    PRIMARY KEY (source_id, target_id),
    FOREIGN KEY(source_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES notes(id) ON DELETE CASCADE
);
CREATE INDEX idx_co_utility_weight ON co_utility_edges(source_id, weight DESC);
```

## Execution pipelines: online vs offline

### Online (post-turn git hook)
A lightweight Python hook runs immediately after a successful git commit:
1. Reads `git log -1` to extract `Prompt:` and the commit diff stats.
2. Inspects recent tool execution logs for note read paths in the current turn.
3. Matches diff tokens against read note terms and logs rows into `session_credit`.
4. Executes in <15ms without adding LLM latency to the user session.

### Offline (nightly sleep consolidation)
Runs during scheduled maintenance per [[grow memory]]:
1. Evaluates complex sessions where deterministic token matching is ambiguous.
2. Applies exponential synaptic decay ($\gamma \approx 0.95$) to `co_utility_edges`, weakening stale connections while preserving active clusters.
3. Identifies high-impression, zero-utility notes as candidates for [[vault synapse pruning]].
4. Flags prompts that resulted in zero useful note retrievals as vault knowledge gaps.

## Storage boundaries: zero markdown pollution

Telemetry and utility metrics must never be written into note [[YAML front matter]].

Writing scores into Markdown files creates immediate systemic failures:
- Pollutes `git log` with machine-generated noise, destroying human provenance (see [[track prompt history]]).
- Updates file `mtime`, breaking Obsidian's recently modified sorting.
- Triggers file watcher loops and stalls automated backups (see [[view count]]).

Keeping all metrics in `pkm_index.db` ensures the Markdown vault remains clean, human-readable, and git-friendly.

## Related notes
- [[2026-08-27 every read is a write - co-retrieval as synapse strength]] — real-time query logging in `searchd`
- [[hosted PKM vector index and note utility]] — cloud and local utility telemetry model
- [[view count]] — human navigation frequency vs agent outcome utility
- [[track prompt history]] — capturing prompt intent and human provenance in git commits
- [[cross-agent session indexing architecture]] — indexing multi-agent transcripts and tool calls
- [[vault synapse pruning]] — using utility scores to safely prune dead notes and broken links
- [[2026-08-27 synapse links vs wikilinks and semantic links]] — comparing dynamic synaptic edges to static wikilinks
- [[grow memory]] — nightly consolidation pass where credit assignment runs
- [[pkm metadata indexer]] — SQLite index schema and search daemon architecture
