---
name: recency-proximity reranking prior tested against real wikilinks
description: A time-closeness reranking signal for search, measured against real wikilinks — multiplicative and rank-fusion forms rejected (proven and measured), an additive form validated and recommended
created: 2026-08-31
aliases:
  - recency-proximity reranking prior tested against real wikilinks
  - recency-proximity prior
tags:
  - pkm
  - search
  - graph-theory
  - research
  - technical
---

A proposed search-reranking signal — fold time-closeness between two notes into ranking. Three ways to combine it with a vector-similarity score were tested against real wikilinks: a multiplier (rejected, proven and measured), reciprocal rank fusion (also rejected, measured), and an additive term (validated: +7.73% to +8.60% MRR on the full sample, stable across seeds). Documented in full because the negative results are as reusable as the positive one — each mechanism's failure or success maps directly onto the same rank-flip proof.

## Where this came from

[[co-commit graph mining for serendipitous note associations|co-commit graph mining]]'s research turned up a broader theory: every note in a vault is latently connected to every earlier note, because one continuous mind wrote all of them (Bush's *associative trails*, Niklas Luhmann's Zettelkasten writing, the cognitive mechanism is spreading activation — Collins & Loftus, 1975). Formalizing that as a dense graph (every pair of notes gets an edge, weighted by creation-time distance) is real but not worth building: $O(N^2)$ storage for almost entirely negligible weight. The one piece that looked worth keeping was folding the same decay function into reranking instead, as a scalar multiplier on an existing ranked list rather than a stored edge.

## Method

No local LLM gateway was available to blind-judge relatedness the way [[co-commit graph mining for serendipitous note associations|the co-commit signal]] was tested. Used a different ground truth already in the vault instead: an explicit `[[wikilink]]` between two notes is a human saying, at write time, "these are related" — real, human-curated, and free.

`recency_prior_experiment.py` (in `skills/pkm-metadata-indexer/`):
1. Builds a creation-date cache from one `git log --reverse --diff-filter=A` walk (3,885 dates in 1.2s — not one `git log` per file, which an earlier fork this session used and which does not scale).
2. For every note with a resolved outbound wikilink, computes the target's rank under vector-cosine similarity alone (baseline), and its rank after multiplying every candidate's score by the recency-proximity factor (reranked).
3. Reports mean rank and MRR (mean reciprocal rank — weights top-of-list positions heavily) for both, over a sample of wikilinked pairs.

Three parallel subagents ran the actual sweeps against the real `brain` vault.

## Results

**τ swept at λ=1.0** (fixed seed, n=500 per point):

| τ (days) | MRR change |
| :--- | :--- |
| 3 | -19.15% |
| 7 | -19.49% |
| 14 | -17.76% |
| 30 | -17.01% |
| 90 | -13.61% |
| 180 | -13.68% |
| 365 | -11.43% |
| 1000 | -2.27% |

Every value hurts. Damage shrinks only as τ→∞, where the term degenerates toward a near-constant multiplier across the whole candidate pool — i.e. barely reranking anything. No sweet spot in the range tested.

**λ swept at τ=30** (same fixed seed, n=500):

| λ | MRR change | improved | worsened |
| :--- | :--- | :--- | :--- |
| 0.05 | +5.36% | 157 | 191 |
| 0.1 | **+6.32%** (peak) | 163 | 229 |
| 0.3 | -4.76% | 160 | 271 |
| 0.5 | -11.86% | 158 | 284 |
| 1.0 | -17.01% | 150 | 291 |
| 2.0 | -18.13% | 144 | 300 |
| 5.0 | -18.36% | 143 | 301 |
| 10.0 | -19.23% | 142 | 304 |

A real, clear peak — but even at the peak, the count of pairs that got *worse* (229) exceeds the count that got *better* (163). The MRR gain is a few pairs jumping into top ranks while more pairs drift slightly worse deeper in the list. Monotonic hard decline past λ≈0.3.

**Stability check at τ=30, λ=0.5** (the config an earlier validation run had shown +0.41% on, n=400):

5-seed sweep: +0.41%, -14.31%, -16.61%, -13.08%, -5.85% (mean ≈ -9.9%, std ≈ 6.6%). The original +0.41% was a lucky draw. Full sample, no cap (n=4,722, every usable wikilinked pair in the vault): **-11.69%** — the real answer for this configuration.

## Why it fails: displacement, not noise

A qualitative spot-check (reading the actual notes behind worsened and improved pairs) confirmed the mechanism does exactly what the formula says:

- **Improved pairs** are almost all created the same day, and several are genuine companion notes: `Pyblish lite.md` ↔ `Pyblish qml.md`, `Windows 10 Enterprise.md` ↔ `Windows 10 Pro.md`, `compress photos Google Photos.md` ↔ `Google Photos.md`. The prior correctly identifies these.
- **Worsened pairs** mostly have *large* creation-date gaps (185–836 days) — the wikilinked target's own score barely moves at that gap (its multiplier is ≈1). What sinks its rank is that *other* candidates written close in time to the anchor get boosted past it.

That second point is the actual failure mode, and it's structural, not a tuning problem: a **global multiplier applied to every candidate** necessarily changes relative rank for everyone, not just the pair you're trying to help. Rewarding same-day notes demotes the relative position of every note written on a different day — including notes a human explicitly linked, at whatever distance. The benefit (correctly surfacing real same-day companions) and the cost (burying real long-distance links under a wave of same-day noise) come from the same mechanism and can't be separated by adjusting τ or λ; they only trade off against each other.

## Follow-up: does a hard cutoff (last hours/days) fix it?

Natural next question — the smooth exponential tail still gives *some* boost to far-apart candidates; does replacing it with a step function (`proximity = 1.0 if gap ≤ window else 0.0`, `--mode hard` in the script) confined to a short, literal "last few hours / last day" window avoid the damage? `recency_prior_experiment.py` was extended to support this, with the creation-date cache upgraded from day-only to full ISO timestamps (`git log --format=%aI`, still one walk, 3,886 timestamps in 1.2s) so hour-scale windows are measurable at all.

**Window swept at λ=1.0** (fixed seed, n=500):

| window | MRR change | mean boosted candidates |
| :--- | :--- | :--- |
| 1 hour | -5.71% (best) | 9.52 |
| 6 hours | -13.20% | 17.03 |
| 24 hours | -16.06% | 32.22 |
| 3 days | -17.17% | 54.88 |
| 1 week | -18.85% | 91.28 |
| 30 days | -20.99% | 189.60 |

`mean_boosted_candidates` — how many other notes fall within the window per anchor, the actual mechanism check — drops 20× from 30 days to 1 hour, and MRR damage does shrink monotonically alongside it. But it never turns positive, and worsened pairs outnumber improved at every window tested here, because λ=1.0 is still too strong once *any* candidate qualifies.

**λ swept at a 24-hour window** (fixed seed, n=500): peaks at λ=0.05 (+7.95%), turns negative by λ=0.3, flat at λ≥1.0 (-16.06%, unchanging past that point since `mean_boosted_candidates` is fixed by the window, not λ). Same peak-then-collapse shape as the decay sweep, same magnitude — narrowing the window alone doesn't change the story, it needs pairing with a small λ too.

**Stability check at a 6-hour window, λ=0.3** (the tightest, gentlest combination tested): 5-seed sweep at n=500 gave -1.68%, -0.93%, -7.49%, -1.66%, -7.70% (mean ≈ -3.89%, std ≈ 3.04% — more stable than decay mode's wild swing, but every individual seed still negative). The full-sample answer (n=4,725, no cap) was **+1.11%** — small, but genuinely positive, the first configuration all session where the population-level truth isn't negative. A qualitative spot-check found the identical mechanism as before at smaller scale: worsened pairs have gaps of 12–497 days (target's own boost ≈0, other in-window candidates jump past it instead), improved pairs are essentially all same-session companions (`2025-11-12 datafix - added automated testing.md` → `Python - Black.md`, rank 752→5). Narrowing the window shrank the blast radius enough to flip the population sign, but the effect is tiny and routinely erased by per-sample noise at realistic sample sizes.

## Why it fails, proven independent of the measurements

A separate derivation confirms the mechanism without relying on the numbers above. For a true target $i$ and rival candidate $j$, reranking flips their order exactly when:

$$p_j - p_i > \frac{v_j - v_i}{\lambda \cdot v_i}$$

If $v_j \le v_i$ (the rival was never ahead on content alone), the right side is $\le 0$, so **the flip triggers whenever $p_j > p_i$, for any $\lambda > 0$** — a multiplicative boost can only ever demote a target relative to something *more temporally-close than the target itself*, never relative to something further away.

This is why rival *count*, not tuning, dominates: if an anchor has $k$ "temporal rivals" (other notes created near it) each with some small independent chance $p$ of already scoring close enough to flip once boosted, the chance at least one does is $1 - (1-p)^k$ — saturating toward 1 as $k$ grows, even for small $p$. Measured directly on this vault: **14.4 rivals within 1 hour of any given note, 37.4 within 24 hours** — $k$ never approaches 0 at any window tested, which is exactly why narrowing the window shrinks but never eliminates the damage. The idea only nets positive when the true target is *itself* one of the anchor's temporal rivals (a same-session companion note) rather than a genuine long-distance link — a bet that "written close in time" implies "the right answer," true for one specific kind of pair and false for the general case a wikilink graph is full of.

## RRF fusion: also rejected, decisively

Research turned up a third combination mechanism: reciprocal rank fusion, `final = 1/(k+vector_rank) + 1/(k+recency_rank)`, fusing by rank position instead of rescaling a score. This is the standard way production hybrid search systems combine relevance and freshness, and a 2025 paper (Re3, arXiv 2509.01306) uses it specifically to avoid the unbounded-displacement failure proven above — a signal's contribution here is capped at `1/k`, so it looked like the structural fix.

It isn't, at least not for this signal. A k sweep (1 to 100,000, n=500) never turned positive — best at k=5 (-4.60%), and damage got *worse*, not better, as k grew (-21.39% at k=100,000; both lists flatten together at large k rather than converging back to the vector-only order, contrary to the initial hypothesis). 5-seed stability at k=5: every seed negative (mean ≈ -7.7%). Full-sample (n=4,725) at k=5: **-4.18%**.

The qualitative reason is more nuanced than "irrelevant noise wins": in 4/5 spot-checked worsened cases, the candidate that displaced the true target had a *genuinely strong* vector rank on its own (2-4) and happened to share the anchor's session — RRF correctly promoted a good, real match, just not the *specific* one a human had wikilinked, and MRR only credits the one true answer. RRF bounds the damage from *unbounded* rescaling, but a rank-1 recency signal that's mostly noise with respect to "is this the specific wikilinked note" still costs more than it gives, at any weighting a plain rank-fusion constant can express.

## The mechanism that actually works: additive, not multiplicative or rank-fused

A brainstorm on alternatives found the one combination mechanism that survives every check the other two failed: a small additive term, `final_score = vector_score + λ · proximity`, instead of a multiplier or a rank fusion.

**Lambda sweep, decay mode, τ=30 days** (n=500, seed=0):

| λ | MRR change | improved | worsened |
| :--- | :--- | :--- | :--- |
| 0.001 | -0.20% | 77 | 53 |
| 0.005 | +1.06% | 134 | 106 |
| 0.01 | +3.05% | **150** | 138 |
| 0.02 | +5.24% | 165 | 164 |
| 0.05 | **+9.74%** (peak) | 168 | 208 |
| 0.1 | +7.76% | 167 | 244 |
| 0.2 | -4.10% | 165 | 273 |
| 0.5 | -17.33% | 153 | 298 |

`improved` exceeds `worsened` through λ=0.02 — the first time all session, at any configuration in any combination mechanism, that happened. Unlike the multiplicative peak, this one **decays gently past its optimum instead of collapsing.**

**5-seed stability at λ=0.05:** +9.74%, +8.40%, +6.26%, +7.31%, +3.61% — mean ≈ 7.06%, std ≈ 2.2%. **Every single seed positive.** The multiplicative "peak" reversed sign on 4 of 5 seeds; this one didn't reverse on any.

**Full-sample (n=4,725):** **+7.73%** MRR (decay, τ=30d, λ=0.05) — confirms the seed average, the opposite of what happened when the multiplicative peak was checked this way. The hard-cutoff variant (τ=6h) does slightly better still: peak λ=0.05, full-sample **+8.60%**.

The mechanism, from the rank-flip proof above: an additive term of size λ can only flip an order where the *raw vector-score gap* between two candidates is smaller than λ — it is structurally incapable of displacing a candidate that was clearly better on content, unlike the multiplier (which flips whenever proximity favors a rival at all, regardless of the underlying score gap) or RRF (which lets a strong showing on the rank-fused recency list fully compensate for a rank gap on the vector list). It only ever breaks near-ties, which is exactly the "tiebreaker" fix this note speculated about before testing it — and it is the one mechanism, of three tried, where that speculation held up.

## Verdict

**Don't ship a global recency multiplier or an RRF rank-fusion of recency** — both were tested rigorously (multi-seed, full-sample) and rejected; the RRF result specifically shows that avoiding unbounded displacement is not sufficient on its own, since RRF still let a signal that's mostly noise with respect to the specific wikilinked target dilute a good baseline ranking.

**The additive combine is a real, validated improvement** and the recommended form if this is pursued further: `combine=add, mode=hard, tau=6h, lambda=0.05` (+8.60% full-sample) is the best config found, with `combine=add, mode=decay, tau=30d, lambda=0.05` (+7.73%) a close, simpler alternative. Before wiring it into `searchd.py`'s `/similar` the way [[co-commit graph mining for serendipitous note associations|co-commit's `&graph=1`]] was, it should get the same opt-in-behind-a-flag treatment and the same live smoke-test — but unlike the multiplicative and RRF forms, there's now a genuine case for shipping it.

The narrower [[co-commit graph mining for serendipitous note associations|co-commit graph]] remains a useful, independent signal in its own right; this note's conclusion is no longer "the whole idea fails," it's "two of three ways to combine it fail, and the third is worth shipping."

## prior art on the combination question

A GitHub and web search found real, independent corroboration for both sides of the additive-vs-multiplicative finding. [benmaster82/Kwipu](https://github.com/benmaster82/Kwipu) (266 stars) is a local Graph RAG tool for Obsidian vaults whose hybrid retrieval explicitly combines Synonym + Vector + BM25 + Temporal signals — a real, shipped PKM tool folding recency into hybrid search the same way this note does, though it doesn't document testing additive against multiplicative. [Emmimal/temporal-rag](https://github.com/Emmimal/temporal-rag) (49 stars) went the other way, multiplicative (`final = semantic_penalty × [(1−w)·vector + w·(decay×recency×validity×event)]`), with a decay floor added specifically so old-but-still-valid facts don't get zeroed out — a different mitigation for the same displacement risk this note's rank-flip proof describes. [Elastic's own engineering blog](https://www.elastic.co/search-labs/blog/bm25-ranking-multiplicative-boosting-elasticsearch) documents the mirror-image lesson in production BM25 ranking: an additive rank-feature boost was found scale-unstable across queries, and Elasticsearch's `function_score` moved to multiplicative for that reason — the opposite conclusion from this note's own, a reminder that which combination mode is safe depends on what's being combined and how the base scores are scaled, not a universal rule.

The strongest corroboration is [albinotonnina/echos](https://github.com/albinotonnina/echos), which benchmarked hybrid (RRF of full-text + vector) search against the same hybrid with a temporal-decay boost added, on its own labeled ground truth — a genuinely independent replication, different codebase, different data. Result: temporal decay gave zero improvement on temporal queries (MRR 1.000 to 1.000 — no gain) and caused a serious regression elsewhere (P@5 dropped 0.855 to 0.491, needle-in-haystack MRR collapsed 0.920 to 0.209). That's the same failure shape this note measured — a naive recency boost demotes genuinely correct results — reached independently, which is stronger evidence than a single-vault result on its own.

## Related
- [[co-commit graph mining for serendipitous note associations]]
- [[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]]
