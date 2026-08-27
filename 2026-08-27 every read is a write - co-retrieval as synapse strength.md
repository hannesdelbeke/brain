---
date: 2026-08-27
created: 2026-08-27
tags:
  - pkm
  - ai
  - architecture
  - search
  - retrieval
  - graph-theory
  - technical
aliases:
  - 2026-08-27 every read is a write - co-retrieval as synapse strength
  - every read is a write
  - co-retrieval logging
  - the missing edge producer
  - Hebbian read logging
---

# Every Read Is a Write: Co-Retrieval Logging as the Producer for Synapse Strength

Instrument the retrieval path so that every query carries the note that asked it, and every returned result records an edge back to that origin with a count. Reading becomes a write. The counts are link strength, they live in SQLite next to the index rather than in the markdown, and they supply the one thing the Hebbian edge design has always been missing: data.

Related: [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], [[public/pkm-search|pkm-search]], [[public/2026-08-27 agentic pkm action plan|agentic pkm action plan]], [[public/vault synapse pruning|vault synapse pruning]], [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]]

---

## 🎯 This Is the Deferred Item's Missing Producer

The action plan puts `synaptic_edges`, Hebbian weighting and nightly decay in P2, with one reason recorded:

> Needs co-retrieval data that nothing logs yet. Log queries and their result sets in `searchd.py` first; weighting an empty table is theatre.

That is this note. The design in [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] describes the consumer — a weighted edge table, LTP on co-activation, LTD on disuse, pruning below threshold. It never named the producer. `searchd.py` already sees every query and every result set; it just throws them away after serialising the response. Adding one parameter and one insert turns the daemon into the write path for the entire synaptic layer, and unblocks every P2 item that depends on it.

Nothing else in the stack is in a position to do this. The indexer only sees files. Obsidian only sees human clicks ([[public/view count|view count]], [[public/2026-02-22 Obsidian track note view|track note view]], [[public/2026-07-22 follow up Obsidian viewcount|follow up on viewcount]]) and misses everything an agent reads, which is now the majority of reads.

---

## ⚙️ The Mechanism

`searchd.py` is resident on `127.0.0.1` serving `/search`, `/links`, `/health` and `/reindex`, hybrid FTS5 BM25 plus 384-dim `bge-small-en-v1.5` vectors fused by reciprocal rank fusion, warm queries at 13–22 ms, against `notes` / `sections` / `links` in `pkm_index.db`.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    READ PATH, INSTRUMENTED                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   AGENT (currently editing note X)                                   │
│      │  GET /search?q=hebbian+decay&origin=X                         │
│      ▼                                                               │
│   searchd.py ──▶ FTS5 BM25 ─┐                                        │
│                             ├─▶ RRF fuse ──▶ results [A, B, C]       │
│                 vectors ────┘                       │                │
│      │                                              │                │
│      │  response (path, line, heading, score)  ◀────┘                │
│      ▼                                                               │
│   async queue ──▶ edges: (X→A, +1), (X→B, +1), (X→C, +1)             │
│                   notes: reads[A]++, reads[B]++, reads[C]++          │
│                                                                      │
│   No origin?  ──▶ skip the edge rows, still bump the read counts     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

Three changes, in order of size:

1. `/search` accepts an optional `origin` (note id or path) and an optional `intent` string.
2. For each result actually returned, upsert one row into `edges` keyed on `(source_id, target_id)`, incrementing `count` and setting `last_seen`.
3. Increment a per-note counter regardless of whether an origin was supplied.

The edge is written for what the daemon returned, not for what the corpus contains. That is the difference between a co-retrieval edge and a semantic-similarity edge: similarity is a property of the text and can be recomputed at any time, co-retrieval is a property of use and is gone forever if not recorded at the moment it happens.

---

## 🧭 Why the Origin Has to Be Passed, Not Inferred

The daemon cannot know what the caller was working on. It sees a query string over a loopback socket. Inferring the origin from the query text means embedding the query and finding its nearest note, which returns the note most similar to the question — which is frequently one of the results. That produces self-edges and edges that encode semantic similarity a second time, in a table meant to encode something similarity cannot express.

So the caller declares it. The agent knows which note it currently has open, which note it is writing, or which note the human pointed at. Passing that string costs nothing and is the only place the truth exists. In practice the origin belongs in the agent's search instructions the same way any other required parameter does; a query without one is accepted, not rejected.

**When there is no origin.** A human typing in a search box. A cold agent at the start of a session with no current note. A `/reindex`-triggered internal query. In all of these, write no edge and increment a plain per-note read counter instead. This anonymous signal is weaker but simpler and still useful: it is the raw popularity of a note, which is exactly what [[public/vault synapse pruning|vault synapse pruning]] wants for dead-synapse detection and cannot currently get for agent reads. A note with zero retrievals in a year is a pruning candidate whether or not anything is known about who asked.

---

## 🔢 Three Counts, Not One

The most common way to get this wrong is to keep one number and call it strength.

| Signal | What it means | Volume | Evidence of usefulness |
|:---|:---|:---:|:---|
| **Retrieved** | The daemon returned it in a result set | Very high | Almost none. Says the ranker liked it |
| **Opened / read** | Something actually read the file after seeing it | Medium | Some. Says a caller judged it worth the tokens |
| **Followed** | The read was succeeded by an edit, a new note, or a cited answer | Low | The real signal |

Only the third is close to evidence that the note did work. Ranking on retrievals alone builds a **rich-get-richer loop**: a note that ranks high gets retrieved, the retrieval increments its weight, the weight feeds ranking, so it ranks higher, is retrieved more, and the loop closes. After a month the top of every result set is whatever happened to rank well in week one, and notes that never got an early impression can never earn one. This is the same pathology as a recommender trained on its own outputs, and it is the failure mode that makes engagement-ranked feeds converge on a handful of items.

Three fixes, usable together:

* **Log all three separately.** `retrieved`, `opened`, `followed` as distinct columns on the same edge row. Never collapse them at write time; collapsing is a ranking decision and belongs at read time where it can be changed.
* **Weight on the scarce signal.** `followed` is orders of magnitude rarer than `retrieved`, which is what makes it informative. Give it the weight.
* **Normalise by impressions.** Divide by retrievals the way click-through rate does: a note opened 4 times out of 5 retrievals is stronger than one opened 20 times out of 900. This alone breaks the loop, because being retrieved constantly now hurts a note that is never used.

Recording `followed` needs the agent to report back after the fact, which is a second call and a real cost. A cheap approximation: if a note appears as an `origin` on a later query within the same session, something consumed it.

---

## 🗄️ The SQL Side

```sql
CREATE TABLE edges (
    source_id   INTEGER NOT NULL,        -- origin note, from the caller
    target_id   INTEGER NOT NULL,        -- note the daemon returned
    retrieved   INTEGER NOT NULL DEFAULT 0,
    opened      INTEGER NOT NULL DEFAULT 0,
    followed    INTEGER NOT NULL DEFAULT 0,
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL,
    PRIMARY KEY (source_id, target_id)
);
CREATE INDEX edges_target ON edges(target_id, retrieved DESC);
```

It belongs in `pkm_index.db` alongside `notes` / `sections` / `links` because it is derived, regenerable in principle, high-churn, and worthless to a human reading a file. Everything with those four properties already lives in the index. Everything in the markdown has the opposite properties: authored, durable, low-churn, meant to be read. Putting a counter in a note body violates all four at once.

**Cost per query.** The read path is currently read-only, and adding a synchronous write to it is the one way to turn a 13–22 ms query into something slower and occasionally locked. Do not write inside the request. Push `(origin, [result ids], timestamp)` onto an in-process queue, return the response, and have a background thread drain the queue every few seconds into a single transaction. Ten results per query and a few hundred queries a day is a few thousand upserts, which is nothing in one batched transaction and a measurable regression as three hundred separate ones. If the process dies with a full queue, the lost data is a handful of reads, which is an acceptable loss for a statistical signal.

---

## 🚫 Do Not Materialise These as Wikilinks

The idea's own phrasing — "it will add hundreds of wikilinks" — is the design fork, and the answer is no.

A note that gains 300 machine-written links stops being a note. It becomes a link dump with a paragraph at the top. Three consequences, all of them already documented in this vault:

1. **Human readability collapses.** The markdown file is the one artifact a person actually reads. [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] rates wikilinks five stars on human readability, which is the entire reason to keep them; a wall of generated links spends that rating for nothing.
2. **The graph becomes a hairball.** The same note names hyper-connectivity as a pathology, not an achievement: when every note links to every note, spreading activation cannot discriminate, and multi-hop retrieval returns 500 notes for every question. More links is not more signal past a point, and generated edges cross that point immediately.
3. **Every write churns git and re-triggers indexing.** A count that updates on every query means a file that changes on every query. That is a git history of machine noise over the top of the human history that [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]] depends on as the deep memory layer, plus a reindex of the note on every touch, plus Obsidian repainting on disk change.

Keep the edges in SQL. Expose them through a `/links?note=X&by=strength` query and, if a human-facing view is wanted, a rendered panel that reads the table live rather than a block of text on disk.

If materialising is ever wanted, constrain it hard: top 3 only, behind an explicit strength threshold and a minimum age, written into one clearly marked block at the bottom of the note between generated-content markers, rewritten by the nightly pass and never mid-query. That is a suggestion mechanism, which is what the earlier design actually asked for — auto-suggesting an explicit wikilink after 30 days of co-retrieval — not a mirror of the table.

---

## 🌙 Decay, So the Table Reflects Now

Without decay the table is a lifetime archive, and a project that consumed six months two years ago outweighs the thing being worked on this week forever.

* **Exponential decay:** a nightly pass multiplying every count by γ ≈ 0.95, halving an untouched edge in about two weeks. Cheap, one `UPDATE`, no extra storage.
* **Sliding window:** keep per-day buckets and sum the last 90. Exact and queryable by period, at the cost of a row per edge per day.

Exponential is the lazy correct default, and it is the same shape as the synaptic homeostasis framing already in the vault: waking hours potentiate, sleep scales everything down proportionally, weak edges fall below threshold and are pruned, strong edges survive with their relative ordering intact. Run it in the same nightly slot as the consolidation agent from [[public/grow memory|grow memory]] and drop rows below the floor so the table stays bounded.

One caveat: decay applies to weight, not to the raw log. Keep `first_seen` untouched so a decayed edge can still answer "when did these two notes first go together".

---

## 🔓 What It Unlocks Once the Data Exists

None of this is buildable today because there is no table. All of it is a query away once there is one.

* **Co-retrieval suggestions.** "Notes usually read with this one", ranked by strength, shown while writing. This is the associative recall a static backlinks pane cannot do.
* **Cluster detection.** Dense mutual-co-retrieval subgraphs are consolidation candidates — the group of notes that always arrive together is one note that hasn't been written yet. This feeds the tier-2 to tier-3 elevation in [[public/grow memory|grow memory]].
* **Dead-note detection.** Zero retrievals over the window, from any origin, human or agent. The empirical version of the dead-synapse test in [[public/vault synapse pruning|vault synapse pruning]], which currently relies on Obsidian view counts that never see agent reads.
* **Better ranking.** A usage prior blended into the RRF fusion, guarded by impression normalisation so it cannot run away.
* **Query archaeology.** Which questions keep getting asked, and which of them keep failing to find a good answer, which is a list of notes that should be written.

---

## 🔒 This Is a Reading Log

The table is a record of what a person and their agents actually read, and when. That is more revealing than the notes themselves — a query log shows what someone was worried about on a given evening, in order.

* The edge table lives in `pkm_index.db`, which is derived data and not committed. It stays out of any published repo, gitignored alongside the rest of the index.
* Do not log raw query strings by default in the same table as the edges. The `(source, target)` pair is the useful signal; the verbatim question is the sensitive part. Log queries separately, or behind a flag, or not at all.
* The counts should never leak into note bodies, which is a second reason the answer to materialising wikilinks is no: a generated block saying a note was read 340 times is a reading log published by accident.

---

## 🥚 v0, and How to Know It Worked

In the shape the action plan uses. Ship less than feels complete.

**Scope:**
1. `/search` accepts an optional `origin`.
2. `edges` table as above, with only `retrieved`, `first_seen`, `last_seen` populated.
3. One row per returned result, written from a background queue, never in the request.
4. A `reads` counter on `notes` incremented for every result including null-origin queries.

**Deliberately not in v0:** decay, `opened` and `followed`, weighting, ranking changes, suggestions, any UI, any wikilink materialisation, any `contradicts` edge. Every one of those is a design decision that is better made against a week of real rows than against an imagined distribution.

**Acceptance:**
* A week of normal use produces a non-empty `edges` table with more than 100 distinct pairs.
* Warm `/search` p95 stays inside 13–22 ms, measured the same way as before the change, with the queue draining.
* `SELECT source_id, target_id, retrieved FROM edges ORDER BY retrieved DESC LIMIT 20` returns pairs that a human looks at and recognises as genuinely related, not as an artifact of one loop hammering one query.
* Kill the daemon mid-session: it restarts and the table is intact.

Then look at the table before designing anything on top of it. The interesting question is not how to weight these edges, it is what the distribution looks like — whether a handful of hub notes dominate, whether the long tail is real signal or single-shot noise, and how many notes have zero rows on either side. That answer changes what is worth building next, and it costs one week of doing nothing.

---

## 🔗 Related Notes
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] — the consumer design this note supplies the producer for
- [[public/2026-08-27 agentic pkm action plan|agentic pkm action plan]] — where Hebbian weighting is deferred, and why
- [[public/pkm-search|pkm-search]] — the daemon the `origin` parameter lands in
- [[public/vault synapse pruning|vault synapse pruning]] — dead-synapse detection that currently cannot see agent reads
- [[public/grow memory|grow memory]] — the nightly pass the decay job shares a slot with
- [[public/2026-08-18 what retrieval costs as a vault grows|what retrieval costs as a vault grows]] — why the read path is worth keeping cheap
- [[public/view count|view count]] — the human-side read counter this generalises past Obsidian
- [[public/pkm metadata indexer|pkm metadata indexer]] — schema and index tables the `edges` table sits beside
- [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]] — the initiative that owns the v0
