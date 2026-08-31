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

## Verdict

Don't ship a global recency multiplier — smooth or hard-cutoff — over the whole candidate pool. The one configuration that crossed into genuinely positive territory (6-hour hard cutoff, λ=0.3, +1.11% on the full sample) is real but marginal: tiny effect size, erased by sampling noise more often than not, not worth the complexity or the risk of the failure mode reappearing on a different vault or corpus size. If the idea is worth revisiting, the fix has to be mechanistic, not a smaller window or constant: apply the recency term only as a **tiebreaker among near-equal vector scores** (so it only ever decides between candidates that were already close, never displacing a clearly-better candidate that happens to be older).

The narrower [[co-commit graph mining for serendipitous note associations|co-commit graph]] — a sparse, explicit signal from real co-edit history, not a dense time-decay function applied to everything — remains the useful special case of the broader "everything is connected" theory. This reranking-prior version of the same theory does not hold up under testing, in either its smooth or hard-cutoff form.

## Related
- [[co-commit graph mining for serendipitous note associations]]
- [[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]]
