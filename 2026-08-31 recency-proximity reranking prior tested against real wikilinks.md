---
name: recency-proximity reranking prior tested against real wikilinks
description: A time-closeness reranking multiplier for search, measured against real wikilinks in this vault and rejected — displacement cost dominates at any useful weight
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

A proposed search-reranking signal — fold time-closeness between two notes into ranking as a multiplier, `final_score = vector_score * (1 + λ · e^(-Δt/τ))` — tested against real data and rejected. Documented here because the negative result is as reusable as a positive one would have been: the mechanism works exactly as designed, and still shouldn't ship.

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

## Verdict

Don't ship a global recency multiplier over the whole candidate pool, at any τ or λ found in this sweep. If the idea is worth revisiting, the fix has to be mechanistic, not a different constant: apply the recency term only as a **tiebreaker among near-equal vector scores** (so it only ever decides between candidates that were already close, rather than displacing a clearly-better candidate that happens to be older), not as a multiplier over every candidate regardless of how well it already matched.

The narrower [[co-commit graph mining for serendipitous note associations|co-commit graph]] — a sparse, explicit signal from real co-edit history, not a dense time-decay function applied to everything — remains the useful special case of the broader "everything is connected" theory. This reranking-prior version of the same theory does not hold up under testing.

## Related
- [[co-commit graph mining for serendipitous note associations]]
- [[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]]
