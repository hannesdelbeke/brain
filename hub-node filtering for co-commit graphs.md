---
name: hub-node filtering for co-commit graphs
description: why raw co-occurrence counts in a co-commit or co-edit graph get dominated by high-degree hub nodes, and the two fixes (hard threshold exclusion vs lift-normalization) with real measured numbers
tags:
  - pkm
  - graph-theory
  - search
  - technical
---

a **hub node** in a co-commit graph is a file or note that gets touched in an unusually large share of commits — a build config, a shared utility, an `AGENTS.md`-style doc, a `current project` tracker. any two files committed alongside a hub end up looking "related" by raw co-occurrence count, even when the only thing they share is that both happened to be touched in the same commit as something that's touched in nearly every commit. this is the same shape of problem word-frequency weighting solves with TF-IDF or PMI: a raw count conflates "these two things are specifically connected" with "one of them is connected to everything."

## why it matters at real scale, not just in theory

on this vault's own co-commit graph, measured directly: 2,040 of 4,251 nodes (48.0%) qualify as hubs at a degree-20 threshold. that's not a rare edge case — on this data, hub nodes are roughly half the graph, so an unfiltered co-occurrence signal is dominated by noise more often than not.

## two fixes, measured against each other

**hard threshold exclusion** — drop any node above a fixed degree cutoff (`z_hub_degree`) before computing co-occurrence. simple, but brittle: the cutoff is an arbitrary number, and setting it too low throws away real signal along with the noise.

**lift-normalization** — score a pair by how much more often they co-occur than *expected* if they were independent (observed co-occurrence divided by the product of their individual frequencies), rather than by raw count. this doesn't need a threshold at all — a true hub gets a low lift score automatically, because its high individual frequency is already priced into the expectation.

measured head-to-head on this vault's own graph (standalone MRR vs. a vector-similarity baseline, real data, n=959 usable pairs): raw co-occurrence **-36.81%**, hard-threshold exclusion **-54.46%** (worse — the cutoff was too aggressive and cut real signal too), lift-normalization **-35.83%** standalone but **+11.81%** in an RRF fusion sweep, against the hard threshold's +6.88% best case. lift-normalization won on every graph tested, not just this one. it's now integrated into this vault's own `co_commit.py` and `co_touch.py` in production, not just an experiment script.

## the same word, a much older literature — and where it doesn't actually match

"hub" is a loaded term here, and the overlap with a big web directory site (Yahoo Directory, the Open Directory Project/DMOZ) that lists hundreds of links by category is real but only partial. those directory hub pages are the *literal* shape of the problem — a page whose entire content is outbound links, exactly like a co-commit hub file that shows up next to nearly everything — but they're valuable *because* they're a hub: a human editor deliberately curated that list. our co-commit hub node is the opposite: a file that co-occurs with everything by incidental necessity (a build config, a shared doc touched in every commit), with no curation behind it. same shape, opposite sign.

the formal academic term comes from [Kleinberg's HITS algorithm](https://en.wikipedia.org/wiki/HITS_algorithm) ("Authoritative sources in a hyperlinked environment," *JACM* 1999) (verified 2026-09-01): a **hub** is a page that links to many good **authorities**, and hub/authority scores mutually reinforce each other. HITS's known failure mode is the **tightly-knit community (TKC) effect**, identified in [Lempel & Moran's SALSA paper](https://dl.acm.org/doi/10.1145/382979.383041) ("SALSA: the stochastic approach for link-structure analysis," *ACM TOIS* 19(2), 2001; also *Computer Networks* 33, 2000) (verified 2026-09-01) — a small, densely interlinked cluster of pages scores as a strong hub/authority community even when it isn't actually authoritative on the topic. that's the same mathematical shape as our hub-node problem: density alone gets mistaken for signal. [SALSA](https://en.wikipedia.org/wiki/SALSA_algorithm) fixes it by decoupling hubs and authorities into two independent random walks instead of one mutually-reinforcing eigenvector computation, and the result is described as equivalent to a *weighted in/out-degree ranking* (verified 2026-09-01) — conceptually the same move as lift-normalization (discount raw connectivity against what's expected), but not the same math: SALSA is a stationary distribution over a bipartite random walk, lift-normalization is a direct observed-over-expected ratio (PMI-style). call this a real but partial parallel, not an equivalence.

the closer literal match to our case is **nepotistic links** — [Davison's "Recognizing Nepotistic Links on the Web"](https://www.academia.edu/539917/Recognizing_nepotistic_links_on_the_web) (AAAI Workshop on AI for Web Search, 2000) (verified 2026-09-01) names exactly this: a page that links indiscriminately (not a curator, just structurally over-connected) pollutes any link-graph signal built on raw counts, and the standard countermeasure researchers converged on is downweighting or pruning those links — the same two options (hard exclusion, or a normalized weight) this note already tested against each other for co-commit graphs, arrived at independently.

## the general lesson, not just this one signal

this is the same shape of fix as [[2026-08-31 recency-proximity reranking prior tested against real wikilinks|the additive-vs-multiplicative recency-reranking result]]: a broad, real-but-diffuse signal (temporal proximity there, raw co-occurrence here) shouldn't be allowed to dominate a ranking undamped — it needs to be bounded, normalized, or only allowed to break near-ties, or it drowns out the specific signal a system actually cares about. both problems have the same underlying cause: something correlated with *almost everything* looks like a strong signal for *anything* unless its baseline rate gets subtracted out first.

## an apparently real, unaddressed gap in existing tooling

a GitHub search across established co-commit and logical-coupling tools — [Hercules](https://github.com/src-d/hercules) (verified 2026-09-01), [code-maat](https://github.com/adamtornhill/code-maat) (verified 2026-09-01), and smaller tools like `LogicalCouplingTool` — found none of them document hub-node filtering or lift-normalization for this exact problem. they detect co-change frequency but don't appear to normalize for files with very high edit frequency. on the evidence of that search, this fix is a genuine, if small, contribution rather than a rediscovery of established practice.

## related
- [[2026-08-31 other candidate relatedness signals for search reranking]] — the full experiment this note's numbers come from, including the z_hub_degree calibration sweep and the lift-normalization-in-production integration
- [[co-commit graph mining for serendipitous note associations]] — the original co-commit signal this fix was applied to
- [[2026-08-31 recency-proximity reranking prior tested against real wikilinks]] — the parallel additive-vs-multiplicative lesson for a different diffuse signal
- [[2026-09-01 prior exposure as an implicit edge - the link between recency reranking and code-authorship expertise]] — where this fix's absence from open-source expertise-mining tools is cited as a novelty point
- [[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]] — the shipped code this fix lives in
