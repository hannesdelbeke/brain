---
date: 2026-08-18
created: 2026-08-18
tags:
  - technical
  - pkm
  - retrieval
  - ai
  - architecture
  - performance
  - tokens
aliases:
  - 2026-08-18 what retrieval costs as a vault grows
  - what retrieval costs as a vault grows
  - vault retrieval economics
  - zettel vs long note retrieval costs
---

# What Retrieval Costs as a Vault Grows: Empirical Token Economics & Architecture

An empirical analysis of retrieval economics across growing Personal Knowledge Management (PKM) vaults—comparing long-form problem notes against flat atomic Zettelkasten systems (`brain`), modeling token costs, proving why within-note chunking is unprofitable, and defining the transition thresholds from lexical Ripgrep to section-level vector embeddings.

Related: [[public/pkm-search|pkm-search]], [[public/pkm metadata indexer|pkm metadata indexer]], [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]], [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]]

---

## 🎯 TL;DR

* **Retrieval cost does not scale with vault size.** A grep plus a sliced read costs about three cents whether the vault holds 1,000 notes or 100,000, because neither the query nor the payload grows with the corpus. What scales is anything that touches every note.
* **Note size and note count drive different costs.** Size drives the body; count drives the index of all filenames. A Zettel convention of short atomic notes buys roughly 8x on the body and nothing on the index, so agentic writing crosses the index threshold within months either way.
* **Do not build within-note chunking.** Break-even is around 5,600 tokens per note and the useful threshold is near 11,000 tokens, while the largest note measured here would save only twelve to forty cents. Grep returns line numbers and `Read` takes an offset, so slicing already costs zero extra API calls.
* **Build one embedding vector per note over titles, and build it for the write path before the read path.** Duplication is the failure that scales worst, since near-duplicate pairs grow with the square of the note count while agents carry nothing between sessions. No GPU and no vector database is warranted below roughly 300,000 notes.
* **What breaks first is recall, not tokens.** Long notes make grep imprecise; short notes make the filename index expensive.

---

## ❓ The Core Question

The common intuition is that a bigger vault costs more to search, so a vault growing at machine speed will eventually become unaffordable to read. That intuition is wrong in an interesting way, and the measurements below identify what actually breaks instead.

The cost unit throughout is established in token economics: an API call, and a tool result priced at:

$$\text{Price} = n \times (1.25 + 0.1 \times R)$$

where $n$ is the token size and $R$ is the number of API calls remaining before the result falls out of context. The tables here use $R = 20$, giving a multiplier of $3.25$, based on agent context auto-compaction plateaus (~166k tokens).

---

## 📈 How Fast a Vault Actually Grows

In an active technical vault:
* **Measured Baseline:** 129 notes in 7 days = **18.4 notes/day**.
* **Bimodal Distribution:** 92 of the 129 notes arrived in five batch commits (e.g. bulk portfolio migrations). Excluding those, hand-directed incremental writing runs at **5.3 notes/day**.
* **Note Size Distribution (Tokens):** Mean: 1,957 | p50: 957 | p90: 4,989 | p99: 12,855 | Max: 15,211. No note reaches 20k tokens.

---

## 🔮 One Year Out Projections

Linear growth brackets the vault at roughly 2,000 to 7,000 notes:

| Regime | Notes at 1 Year | Vault Body Size |
|:---|:---:|:---:|
| Incremental Only (5.3 / day) | 2,058 | 4.0M tokens |
| Current Mean (18.4 / day) | 6,855 | 13.4M tokens |

Anchoring on agent session frequency (~48.6 agent sessions/day):

| Assumption | Notes / Day | Notes at 1 Year |
|:---|:---:|:---:|
| 50% of sessions write 1 note | 24.3 | 8,993 |
| Every session writes 1 note | 48.6 | 17,858 |
| Every session writes 3 notes | 145.7 | 53,315 |
| Every session writes 10 notes | 485.7 | 177,415 |

---

## 💸 The Cost That Does Not Scale

Retrieval cost is flat with respect to vault size. A grep followed by reading one note costs about $0.03 whether the vault holds 1,000 notes or 100,000 notes.

**What scales is anything that touches every note:**

| Operation | 1k Notes | 10k Notes | 50k Notes | 100k Notes |
|:---|:---:|:---:|:---:|:---:|
| **Filename index injected once** | $0.18 | $1.79 | $8.94 | $17.88 |
| **Whole vault read** | $32.00 | $318.00 | $1,590.00 | $3,180.00 |
| **Notes matching common term (`agent`)** | 403 hits | 4,031 hits | 20,155 hits | 40,310 hits |

> [!TIP]
> **Rule of Thumb:** Stop injecting full filename indexes once the vault crosses ~5,000 notes.

---

## 🔍 What Breaks First is Recall, Not Tokens

Grep hit density scales linearly with note count:

| Search Term | Notes Matched (129-note sample) | Share | Projected at 10k Notes |
|:---|:---:|:---:|:---:|
| `note` | 114 | 88% | 8,837 |
| `system` / `game` | 100 | 78% | 7,751 |
| `agent` | 52 | 40% | 4,031 |
| `cost` | 38 | 29% | 2,945 |
| `token` | 27 | 21% | 2,093 |
| `cache` | 14 | 11% | 1,085 |

At 10,000 notes, a single common term returns thousands of paths. Grep stops being a retrieval tool and becomes a way to overflow the context window.

---

## ✂️ Why Within-Note Chunking is Not Worth Building

Splitting a long note into chunks to return only the relevant part fails on the arithmetic:
* An extra retrieval round-trip costs ~$0.07 (~14,000 base-input-equivalents).
* With $P_c$ as round-trip cost, $m$ as injection multiplier, $f$ as fraction returned, and $I$ as index overhead:
  $$\text{Break-even Note Size } N > \frac{P_c / m + I}{1 - f}$$
* At $f = 0.2$ and $I = 200$, the break-even note size is **5,635 to 8,028 tokens**.
* Requiring a net saving of at least one extra call puts the useful threshold near **11,000 tokens** (p98.5 of notes). Chunking the largest 15,211-token note saves only $0.12. 90% of notes are a net financial loss to chunk.
* **The Free Baseline:** Grep returns file paths with line numbers, and `Read` takes `offset` and `limit`. Slicing by line range already costs zero extra round-trips.

---

## ⚡ The Index That is Worth Building (and When)

What degrades at 10,000 notes is recall, so the right architecture is a **semantic index over `##` sections** that returns paths and line numbers only, never full note bodies (~150 tokens per hit).

### Hardware Reality:
* 10,000 notes $\times$ 6.8 headings/note = **68,000 sections**.
* 68,000 vectors $\times$ 768 dimensions in `float32` = **215 MB** (~52M multiply-accumulates).
* This takes **< 1 ms in NumPy on a CPU**, compared to an API round-trip of 1–3 seconds.
* **Conclusion:** No GPU and no specialized vector database is warranted below roughly 300,000 notes (1,000,000 chunks). In-memory NumPy dot-product over SQLite float32 blobs is optimal.

---

## 🏛️ Comparison: Long-Note Vault vs. Flat Zettelkasten (`brain`)

| Metric | Long-Note Vault | Flat Zettelkasten Vault (`brain`) |
|:---|:---:|:---:|
| **Total Notes** | 129 | 3,113 |
| **Total Body Tokens** | 253k tokens | 751k tokens |
| **Mean Note Size** | 1,957 tokens | 241 tokens |
| **p50 / p90 / p99** | 957 / 4,989 / 12,855 | 76 / 387 / 2,161 |
| **Max Note Size** | 15,211 tokens | 33,068 tokens |
| **Filename Index Cost** | 10,938 tokens / 1k notes | 5,298 tokens / 1k notes |
| **Historical Growth** | 18.4 / day (7 days) | 2.3 / day (3.7 years) |

In a flat Zettelkasten (`brain`):
1. **The Filenames Are the Semantic Index:** Strict naming conventions carry topic structure. All 3,113 titles cost only ~16.5k tokens ($0.27) to inject.
2. **Whole Vault Fits in Context:** 751k tokens fits in a single Gemini context window for global one-shot link repair or taxonomy passes.
3. **Grep Stays Precise:** Atomic 241-token notes don't suffer keyword cross-contamination.

---

## 🚦 Architectural Triggers to Act On

1. **Build Section Index:** When common search terms match > 50 files, or full title index exceeds > 50,000 tokens.
2. **Build Write-Path Title Index First:** Embed intended note titles before writing to detect near-duplicates and append to existing notes instead of creating duplicates.
3. **Set Agent Note Constraints:** Cap agent note size in `AGENTS.md` to one atomic claim per note that links out rather than expanding endlessly.

---

## 🔗 Related Notes
- [[public/pkm-search|pkm-search]] — resident search daemon and fast hybrid query engine
- [[public/pkm metadata indexer|pkm metadata indexer]] — SQLite indexer, schema, and hybrid ranker
- [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]] — using Git history as the deep memory layer
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]] — Hebbian co-retrieval and dynamic edge weighting
- [[public/obsidian search and index slow on 5k notes|obsidian search and index slow on 5k notes]] — performance optimizations for large vaults
