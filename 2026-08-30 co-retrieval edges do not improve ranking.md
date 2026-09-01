---
date: 2026-08-30
created: 2026-08-30
tags:
  - search
  - evaluation
  - embeddings
  - pkm
---

> [!summary] eli5
> the daemon logs every search, and notes that keep coming back together in one result set can be turned into edges. the question was whether adding that weight to the ranking makes results better. measured: no.
> no bonus weight moves nDCG@10 by more than 0.02, the sign of the effect flips between neighbouring weights, and the best cell of 21 tried has p(Δ>0) of 0.89, which is what ten questions give by chance. underneath that, 97% of the query log is machine traffic: one benchmark query run 2,870 times is half of all pair mass.
> **needs from you:** nothing. the feature is not built and the log needs months of real use before the question is worth asking again.

> [!todo] next
> **next:** ask again when the log holds a few thousand human searches, with the judge running so the evaluation pool can be refilled against the current index.
> **blocked:** the llm judge [[eval_rerank.py]] needs is not running anywhere, so the harness cannot score a fresh pool.

**why:** [[2026-08-30 what else the index can answer]] ranked this second of six, behind missing links. it is the first of the six to be measured and dropped.

## what was being tested

[[co_retrieval.py]] reads `~/.pkm/queries.jsonl`, adds a point to every unordered pair of distinct notes that shared a result set, and decays each pair from its own last sighting with a 30-day half life. the proposal was to add that weight to the fused score at query time, so notes that keep being retrieved together rank together.

the experiment: for each evaluation question take the top 100 fused hits, use the first five distinct notes as pseudo-relevant seeds, give every candidate a bonus equal to the summed decayed edge weight between it and those seeds, normalise the bonus per query, and re-sort by `score + w * bonus`. fused scores sit in a 0.016–0.033 band, so `w = 0.02` is a bonus the size of the whole score spread and `w = 0.2` decides the order outright.

## the numbers

baseline MRR 0.708, nDCG@10 0.754, precision@5 0.495 over ten questions and 105 judged sections.

| w | nDCG@10, edges as they are | nDCG@10, machine traffic removed |
| --- | --- | --- |
| 0.002 | 0.755 | 0.752 |
| 0.005 | 0.735 | 0.773 |
| 0.010 | 0.730 | 0.772 |
| 0.020 | 0.747 | 0.715 |
| 0.050 | 0.746 | 0.711 |
| 0.200 | 0.751 | 0.716 |

the two columns disagree about which end of the range is good: the edges as they are are worst at 0.005–0.010 and best at 0.200, the cleaned edges are the other way round. no monotone region, no shared peak, every value within ±0.043 of baseline, and at no weight do more than three of ten questions improve. that is the shape of noise, not of a signal with a badly chosen coefficient.

## why the evidence is thin, which is the more useful finding

the query log had 8,338 rows folded into the edge database, and 8,335 of them were written on one day, 95% of them less than a second apart.

| category | rows | share |
| --- | --- | --- |
| one query, `battery mode solar`, repeated | 2,870 | 34% |
| numbered soak and benchmark sweeps | 5,202 | 62% |
| everything else | 266 | 3% |

the unit tests write to a temporary log, so this is not test pollution — it is the benchmark and soak loops from the concurrency work in [[2026-08-30 one daemon, several agents asking at once]], run against the live daemon. the damage is worse than the row share suggests, because pair mass grows with the square of the result set: that one query contributes 129,150 of 262,136 pair increments, 49.3%, and owns all five heaviest edges. the whole log touches 310 of 3,081 notes.

so the 4,884 pairs an earlier pass counted are mostly one benchmark query run 2,870 times. a co-retrieval signal needs repeat traffic over the same notes from *different* queries, and there are 266 such rows.

## two defects the measurement found

**the corpus key on a multi-corpus search.** a search over several corpora logged one row naming the corpus as the two names joined by a comma, so its edges landed in a bucket no single-corpus reader matches — 1,227 of them — and pairs could span two corpora that share nothing. the daemon now writes one log row per corpus, each holding only that corpus's paths. fixed on 2026-08-30 with a test.

**the harness cannot see a reorder.** [[eval_rerank.py]] reports precision@limit, and precision at k where k is the request limit is invariant under reordering: the same ten sections in a different order give the same fraction. its headline metric is blind to every rerank it exists to judge. only its mean-first-useful-rank column moves. this measurement used MRR, nDCG@10 and precision@5 instead; the harness should gain one of them before it is trusted again.

a third thing to remember rather than fix: the fourteen evaluation questions are themselves in the query log, so the edge database already holds edges derived from the questions under test. it changed nothing measurable here, but any future run has to exclude them or it is scoring itself.

## what would change the answer

a few thousand human searches in the log, the judge running so the evaluation pool can be refilled against the current index rather than reconstructed from cached verdicts written against an index that has since moved, and a rank-sensitive metric in the harness. until then the honest position is that co-retrieval edges are a real thing the log can produce and an unproven thing to rank with.

related: [[2026-08-30 what else the index can answer]] for the ranking this came off, [[2026-08-30 a semantic graph over the whole vault]] for the edge source that did earn its cost, and [[2026-08-29 one obsidian plugin over the search daemon]] for what consumes the ranking.
