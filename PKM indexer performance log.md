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

Empirical performance telemetry, per-phase timing breakdown, throughput benchmarks, and historical execution logs for the **[[pkm metadata indexer]]** (`public/skills/pkm-metadata-indexer/index_pkm_meta.py`).

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

**Query cold start.** A single `search_vault.py` call takes 3.0s end to end on a warm DB, and nearly all of it is loading the embedding model to encode one query string. The per-call cost is fixed, so it does not improve with a smaller vault or a narrower query, and it is the measurement behind keeping the model resident in the [[lightning-fast unified search plugin for obsidian|search daemon]].

---

## 3. How to Check Live Index Telemetry & Stats

### View Performance History via CLI
Run the `--perf` or `--stats` flag to display database metrics and the latest run performance log:
```bash
python public/skills/pkm-metadata-indexer/index_pkm_meta.py --perf
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
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer SKILL]] — architecture documentation for the SQLite hybrid search engine.
- [[public/pkm metadata indexer|pkm metadata indexer]] — hub note for search scripts and tools.
- [[offline GPU embeddings with incremental cache]] — GPU compute implementation for local vector indexing.
- [[public/agentic tooling upgrades over grep|agentic tooling upgrades over grep]] — benchmarking vector and FTS5 search against standard ripgrep.
- [[token efficient PKM analysis architecture]] — optimizing local compute pipelines for autonomous coding agents.
