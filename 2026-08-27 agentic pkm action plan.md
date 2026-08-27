---
date: 2026-08-27
created: 2026-08-27
tags:
  - pkm
  - ai
  - agentic
  - architecture
  - planning
aliases:
  - 2026-08-27 agentic pkm action plan
  - agentic pkm action plan
  - agentic vault action plan
  - what to build next in the vault
---

# Agentic PKM Action Plan

A cross-initiative plan over the agentic-PKM notes written on 2026-08-27. The three living progress notes each track one initiative; this note sequences work **across** them and records what was verified against the actual repos rather than asserted in prose.

Related: [[public/progress - agentic biomimetic vault|progress - agentic biomimetic vault]], [[public/progress - local-first search daemon and indexer|progress - local-first search daemon and indexer]], [[public/progress - fearless vault consolidation and pruning|progress - fearless vault consolidation and pruning]], [[public/living progress notes over calendar logs|living progress notes]]

---

## 📋 What the notes claim vs what the repos contain

Checked on 2026-08-27 against `pkm-search` (working tree) and the `brain` vault.

| Claim in notes | Actual state | Consequence |
|:---|:---|:---|
| Idle CPU burn: levers "identified", one of them a direct `ort.SessionOptions` with `session.intra_op.allow_spinning=0` | That lever was unreachable: embeddings run through `fastembed.TextEmbedding`, which accepts no `SessionOptions`. Its own `threads=` argument reaches the same pool | Fixed 2026-08-27. `get_embedding_model()` takes `threads`, part of the model cache key, and the query path passes 1; bulk indexing keeps the full pool. Warm idle daemon reads 0.000 cores, pinned by a test |
| `urgent_tasks.py` documented in the pkm-metadata-indexer skill (section 8) | Present in the skill, which is now the only copy of the tool | Resolved. The `pkm-search` repo it was missing from is a README pointing at the skill |
| `python _scripts/check_dead_links.py <note>` is a mandatory pre-publish step | Script now exists (`_scripts/check_dead_links.py`, added 2026-08-27) | Resolved. Run it in the promotion SOP rather than describing it |
| Public notes link as `[[public/<note>]]` | `brain` is mounted at `public/` inside a private parent vault by directory junction, not as a submodule — a submodule would commit a pointer to `brain` into the private repo's history. Opened standalone there is no parent, so every `public/`-prefixed link (90 notes) resolves to nothing | Fine inside the parent vault, broken for standalone/published browsing. Decide which context is authoritative before mass-editing links |
| `profile.md` (living user profile) and `memory.md` (episodic log) | Neither file exists in either vault | Phase 1 of the AI-buddy architecture is unstarted; everything downstream depends on it |
| In-memory NumPy search <1ms over 68,000 sections; no vector DB below ~300k notes | Consistent with [[public/2026-08-18 what retrieval costs as a vault grows|retrieval economics]] | `sqlite-vec` evaluation is a solution without a problem. Defer |
| Vault at 3,113 notes | 3,253 markdown files today | Growth is real but slow at the human-authored rate; the filename-index threshold (~5k notes) is still months out |

---

## 🥇 P0 — Do these before writing another architecture note

### 1. Actually fix the idle CPU burn — done 2026-08-27
* **Where:** `skills/pkm-metadata-indexer/index_pkm_meta.py`, `get_embedding_model()`.
* **What:** `threads` argument passed into `TextEmbedding(...)` and made part of the model cache key. The query path sets `QUERY_THREADS = 1`; bulk indexing leaves it unset and keeps the full pool. No `SessionOptions` and no `OMP_WAIT_POLICY` needed — the fastembed argument reaches the same pool, which is why the session-config entry the earlier notes named was never applied.
* **Acceptance, met:** warm daemon idle over 20s reads 0.000 cores against 11.93 before, at 3.8ms to 8.6ms per encode inside a 13-22ms query. `python -m unittest test_index_pkm_meta test_searchd` fails if the query path stops passing it.
* **Owner note:** [[public/progress - local-first search daemon and indexer|search daemon progress]].

### 2. Build the nightly consolidation agent, v0
The buddy architecture is five capabilities deep on paper and zero deep on disk. Build the smallest version that produces a file a human reads tomorrow morning.

* **Scope:** one script, one cron entry, two files (`profile.md`, `memory.md`), one fast model.
* **Input:** today's git commits across the tracked repos plus any notes created today.
* **Output:** append one dated block to `memory.md` (what happened, what was decided, what is unfinished) and rewrite the changed sections of `profile.md`.
* **Deliberately not in v0:** proactive surfacing, trigger heuristics, contradiction detection, confidence scores. Those are worth building once a week of real `memory.md` entries exists to test them against.
* **Acceptance:** seven consecutive days of entries written without hand-holding, and one instance where the digest surfaced something forgotten.
* **Owner note:** [[public/progress - agentic biomimetic vault|agentic biomimetic vault progress]].

### 3. ~~Reconcile the two copies of the indexer~~
Done 2026-08-27: `skills/pkm-metadata-indexer/` is the only copy, and the `pkm-search` repo is a README pointing at it.

---

## 🥈 P1 — Next, once P0 is verified

### 4. Write-path near-duplicate gate
Embed the intended title before a note is written and refuse or merge on a close match. Both [[public/2026-08-18 what retrieval costs as a vault grows|retrieval economics]] and the search progress note name this as the failure that scales worst: near-duplicate pairs grow with the square of note count and agents carry nothing between sessions. At 3,253 notes and rising it is cheap now and expensive later.

### 5. Section-level SHA256 invalidation
Re-embedding a whole note because one heading changed is the main cost in incremental reindexing. Change the schema in `index_pkm_meta.py` from note-level to section-level hashes.

### 6. Decide the link convention, once
Pick one: keep `public/`-prefixed links and treat the private parent vault as the only valid reading context, or strip the prefix and make `brain` self-contained. Do not mass-edit 89 notes until that decision is written down. The lazy option is to leave the prefix and fix the *published* view instead, since the prefix is correct where the notes are actually authored.

---

## 🥉 P2 — Deferred, with the reason recorded

| Idea | Why it waits |
|:---|:---|
| `synaptic_edges` table, Hebbian weighting, nightly decay | The producer exists as of 2026-08-27: `searchd.py` appends every query and its result paths to `~/.pkm/queries.jsonl`. Build the consumer once the log holds a few weeks of real use, since weighting a table built from a day of it is theatre. [[public/2026-08-27 every read is a write - co-retrieval as synapse strength|every read is a write]] designs it |
| Inhibitory / `contradicts` edges | Same dependency, plus no contradiction detector exists |
| `sqlite-vec` migration | The vault's own measurements say NumPy is under 1ms and no vector DB is warranted below ~300k notes. Revisit at 300k or when a cold query is measurably slow |
| Local Mem0 evaluation | [[public/2026-08-27 Mem0 memory architecture - cloud pricing, security, and local privacy|the Mem0 note]] already concludes local-first. A 200-line append-only `memory.md` is the cheaper test of the same idea. Revisit only if v0 extraction quality is the bottleneck |
| Semantic diff search over git history | Useful, but it serves recall of pruned material — which only matters after aggressive pruning actually starts |
| Automated multi-stub merger | Run one manual consolidation pass first to learn what the merge rules should be, then automate |

---

## 🚧 Anti-goals for this cycle

The vault documents its own failure mode: meta-tool building as displacement activity ([[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]], honesty triggers). Seven architecture notes were written on 2026-08-27. Zero lines of the architecture they describe were shipped.

Rules for the next cycle:
1. No new PKM-architecture note until P0 items 1 and 2 are done and verified.
2. Any progress note that claims something works carries the command that proves it.
3. Prefer editing an existing note over adding one — see [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]].

---

## 🔗 Related Notes
- [[public/living progress notes over calendar logs|living progress notes over calendar logs]] — the initiative-hub convention these three progress notes follow
- [[public/grow memory|grow memory]] — the 3-tier consolidation ladder the nightly agent implements
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] — source of the deferred synaptic weighting design
- [[public/pkm-search|pkm-search]] — the daemon the P0 fix lands in
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]] — the skill whose commands need reconciling with the repo
