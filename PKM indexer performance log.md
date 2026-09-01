---
date: 2026-08-22
aliases:
  - PKM indexer performance log
  - pkm indexer benchmark
  - indexer performance telemetry
tags:
  - technical
  - pkm
  - benchmark
  - performance
  - sqlite
---
> [!quote] User Prompt
> *add the log updates to the indexers to a sep ntote*

Empirical performance telemetry, per-phase timing breakdown, throughput benchmarks, and historical execution logs for the **[[pkm metadata indexer]]** ([[index_pkm_meta.py]]).

---

## 1. Indexing Pipeline Architecture & Phase Breakdown

The indexer measures four distinct execution phases using high-resolution monotonic timers (`time.perf_counter()`):

```
[Markdown Files (6,598)] 
       │
       ▼ (Phase 1: 5.6s - 6.0s @ ~1,150 notes/sec)
[Frontmatter + AST Sections + Graph Edges (23,480+)]
       │
       ▼ (Phase 2: 0.01s - 0.02s)
[Incremental SHA256 Cache Check] ──(Unchanged: 17,544)──> [Skip Embedding]
       │ (New / Modified)
       ▼ (Phase 3: ~2.2s for diffs @ ~5-15 vec/sec)
[DirectML ONNX GPU Embedding (bge-small-en-v1.5)]
       │
       ▼ (Phase 4: 2.5s - 3.0s @ ~16,000 records/sec)
[SQLite WAL Commit + FTS5 Full-Text Rebuild]
```

### Phase 1: Vault Scan & Frontmatter/Link Parsing
- **What it does:** Traverses all vault directories (ignoring `.obsidian`, `.git`, `.venv`), parses YAML frontmatter metadata (`energy`, `sentiment`, `tags`), extracts `[[wikilinks]]`, and chunks sections under `## ` headings.
- **Throughput:** ~1,100–1,200 notes/sec and ~3,800–4,200 links/sec.
- **Typical Duration:** ~5.6s – 6.0s across 6,598 notes.

### Phase 2: Incremental Vector Cache & Diff Filtering
- **What it does:** Compares section SHA256 hashes against existing vector records in `.obsidian/pkm_index.db`.
- **Throughput:** Instantaneous in-memory dictionary lookup.
- **Typical Duration:** ~0.01s – 0.02s across 17,557 sections.

### Phase 3: Neural Vector Embedding Generation
- **What it does:** Computes 384-dimensional dense vector embeddings using `fastembed` (`BAAI/bge-small-en-v1.5`) in batches of 32.
- **Hardware Acceleration:** Uses `DmlExecutionProvider` (DirectML GPU on Windows) with automatic fallback to `CPUExecutionProvider`.
- **Throughput:**
  - Full Cold Build (17,354 vectors): ~3 hours initial background build.
  - Incremental Diff (10–30 modified sections): ~2.0s – 2.5s total turnaround.
  - All Up-to-Date: 0.00s (completely bypassed).

### Phase 4: SQLite Database Transaction & FTS5 Rebuild
- **What it does:** Writes `notes`, `sections`, and `edges` in batch transactions; synchronizes `sections_fts` and `note_titles_fts` full-text search indexes.
- **Throughput:** Writes ~47,000+ relational records and FTS entries in under 3 seconds.
- **Typical Duration:** ~2.5s – 3.1s.

---

## 2. Recent Execution Telemetry (Logged from `index_runs`)

The indexer automatically records each run into the `index_runs` table in `.obsidian/pkm_index.db`:

| Run ID | Timestamp (UTC) | Status | Notes | Sections | Links | Total Duration | Scan / Parse | Embedding | DB Commit | Active Provider |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **18** | 2026-08-22 07:57:00 | `complete` | 6,598 | 17,557 | 23,483 | **11.07s** | 5.98s | 2.28s (13 new) | 2.58s | `DmlExecutionProvider` |
| **17** | 2026-08-22 07:55:58 | `complete` | 6,597 | 17,544 | 23,474 | **10.65s** | 5.60s | 2.18s (2 new) | 2.71s | `DmlExecutionProvider` |
| **16** | 2026-08-22 07:55:29 | `complete` | 6,597 | 17,543 | 23,474 | **10.19s** | 7.39s | 0.00s (cached) | 2.59s | `None` (0 to embed) |
| **15** | 2026-08-22 07:53:34 | `complete` | 6,597 | 17,543 | 23,474 | **~9.1s** | ~5.8s | 0.00s (cached) | ~2.6s | Legacy run |
| **14** | 2026-08-22 07:45:52 | `complete` | 6,596 | 17,544 | 23,474 | **~10.4s** | ~6.0s | ~1.8s (15 new) | ~2.6s | Legacy run |

---

## 2b. Cold Build on a Fresh Clone (2026-08-24, second machine)

A full build of this vault from a fresh `git clone`, every section embedded because the DB does not travel with the repo:

| Notes | Sections embedded | Records written | Total | Embedding | Throughput | Provider |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 3,228 | 6,550 | 19,044 | **41.79s** | 39.50s | **165.8 vec/sec** | `DmlExecutionProvider` |

That is the number to compare a cold build against, and it makes the "~3 hours initial background build" above (roughly 1.6 vec/sec) diagnostic rather than expected: at that rate the embedding ran on CPU.

**The DirectML clobber.** `onnxruntime-directml` and plain `onnxruntime` install into the same package directory and overwrite each other's `onnxruntime.dll`. `fastembed` depends on plain `onnxruntime`, so installing or repairing fastembed *after* the DirectML build silently replaces the GPU runtime with the CPU one, leaving an orphaned `DirectML.dll` behind as the only trace. Providers then report as `['AzureExecutionProvider', 'CPUExecutionProvider']` and everything still works, only a hundred times slower. Check and repair:

```bash
python -c "import onnxruntime; print(onnxruntime.__version__, onnxruntime.get_available_providers())"
# want: 1.24.4 ['DmlExecutionProvider', 'CPUExecutionProvider']
python -m pip uninstall -y onnxruntime onnxruntime-directml
python -m pip install --no-cache-dir onnxruntime-directml
```

Order matters: DirectML last. Any later `pip install fastembed` re-pulls the CPU wheel and clobbers it again.

**Query cold start.** A single [[search_vault.py]] call takes 3.0s end to end on a warm DB, and nearly all of it is loading the embedding model to encode one query string. The per-call cost is fixed, so it does not improve with a smaller vault or a narrower query, and it is the measurement behind keeping the model resident in the [[lightning-fast unified search plugin for obsidian|search daemon]].

---

## 2c. Where a Query Actually Spends Its Time (searchd.py)

Per-stage cost of one hybrid query against the 6,550 vector index, which is what turned a 3.0s CLI call into a 20-60ms HTTP call:

| Stage | Cost | Notes |
| :--- | :--- | :--- |
| Model load | 2.17s DirectML, 0.24s CPU | once, at daemon startup |
| Encode one query | 57–100ms DirectML, 4–38ms CPU | a batch of one never fills the GPU |
| Read + stack every vector | 22ms + 10ms | 10.1 MB, cached in the daemon and rebuilt only when `PRAGMA data_version` moves |
| Cosine + argsort over 6,550 | 0.4ms | the part that sounds expensive and is not |
| FTS5 BM25 with `snippet()` | 0.6–17.6ms | grows with how many rows the OR-expanded query matches |

Three findings, in order of how much they moved the number.

**The GPU is the wrong device for a single query.** Encoding one short string costs 57–100ms on `DmlExecutionProvider` against 4–38ms on `CPUExecutionProvider`, because dispatch dominates when the batch is one row. Bulk indexing keeps the GPU, where batches are 32 and DirectML runs at 165 vec/sec. The split lives in `QUERY_PROVIDERS`.

**Beware the warm-loop benchmark.** Timing the encode in a tight five-iteration loop reported 3.6ms, roughly twenty times better than the same call makes in a real request, because the loop kept the pipeline saturated. Insert an idle gap between iterations or the measurement flatters the GPU.

**Re-reading the vectors was the largest fixable cost.** `search_index` loaded and stacked all 10.1 MB per call. Holding the matrix resident took brain queries from ~100ms to ~21ms; `load_vectors` was split out so the daemon can hand one in and the CLI keeps its old behaviour.

**The gap between a 20ms query and a 60ms one was idleness, not FTS5.** The FTS5 line above reads as the remaining cost and it is not: measured per operator, `battery` costs 0.7ms and the worst natural-language query in the vault costs 12.4ms. What actually moved was the encode, which costs 3.6ms while the pipeline is saturated and 9.5–34.5ms one second later. A keepalive thread encoding `"."` every 250ms holds it at 3.6–3.8ms for about 1.5% of one core, and it skips a tick whenever a real query just ran so it never queues ahead of a user. Idle gaps of 0s, 1s and 2s now return the same number.

**Dropping common terms is worth more than the AND that looks obvious.** Rewriting the OR into an AND is the reflex and it is wrong, because a natural-language query then matches nothing at all. Term frequencies do the same job without the recall cliff: an `fts5vocab` shadow table over the existing index gives a document count per term in 0.1–0.4ms, and anything appearing in more than 10% of sections is dropped before the query is built.

| Query | Full OR | Common terms dropped |
| :--- | :--- | :--- |
| `notes on feeling overwhelmed by projects` | 11.5ms | **3.4ms** (`on`, `by` dropped) |
| `how do i keep the index up to date` | 17.6ms | **2.4ms** (kept `keep index date`) |
| `obsidian plugin search` | 3.8ms | 4.1ms (nothing common enough to drop) |
| `battery` | 0.6ms | 0.7ms (a single term is never pruned) |

Ranking improves alongside the timing, since the dropped words were contributing BM25 noise. If every term is common the rarest one survives, so no query is left with an empty expression.

**Where a query stands now.** 13–22ms server-side against the 6,550 section vault, flat across idle gaps. A shell call through [[search_vault.py]] is 0.61s, of which roughly 0.5s is Python starting up: it is a daemon client first, so `numpy` and `fastembed` are imported only when it has to fall back to searching in-process.

---

## 3. How to Check Live Index Telemetry & Stats

### View Performance History via CLI
Run the `--perf` or `--stats` flag to display database metrics and the latest run performance log:
```bash
python skills/pkm-metadata-indexer/index_pkm_meta.py --perf
```

### Direct SQLite Query for Performance Trends
Query the historical run logs directly using SQLite:
```sql
SELECT 
    id,
    completed_at,
    note_count,
    section_count,
    ROUND(duration_seconds, 2) AS total_sec,
    ROUND(scan_seconds, 2) AS scan_sec,
    ROUND(embed_seconds, 2) AS embed_sec,
    ROUND(db_seconds, 2) AS db_sec,
    provider
FROM index_runs
ORDER BY id DESC
LIMIT 10;
```

---

## Top Relevant Notes
- [[skills/pkm-metadata-indexer/SKILL|pkm metadata indexer SKILL]] — architecture documentation for the SQLite hybrid search engine.
- [[pkm metadata indexer]] — hub note for search scripts and tools.
- [[offline GPU embeddings with incremental cache]] — GPU compute implementation for local vector indexing.
- [[agentic tooling upgrades over grep]] — benchmarking vector and FTS5 search against standard ripgrep.
- [[token efficient PKM analysis architecture]] — optimizing local compute pipelines for autonomous coding agents.
