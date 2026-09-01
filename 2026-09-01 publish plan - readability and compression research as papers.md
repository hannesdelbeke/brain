---
name: publish plan - readability and compression research as papers
description: which vault notes are strong enough to publish as an independent researcher, where to submit them, and what's missing before submission
created: 2026-09-01
tags:
  - pkm
  - research
  - writing
  - meta
---

> see which notes in the vault could be a base to publish a paper, recommend where to publish as an independent researcher, and make a publish plan for each candidate

two clusters in this vault are real candidates. neither is submittable as-is; both have a named, closeable gap.

## candidate 1: the compression benchmark, as an empirical study

**base notes:** [[2026-08-31 research on compressing llm reasoning and notes without losing information]], [[2026-08-31 classifier-based compression with an adversarial fidelity gate]], [[2026-09-01 note-compress skill - design, adversarial review, and bench data]], [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]].

**why it's strong:** a real method (two-pass classify-and-cut plus adversarial score) benchmarked against a real baseline (a rule-based compressor) on real notes, followed by a live-corpus test against 151 eligible notes that produced a genuine negative result — link and number density don't predict which notes compress safely, fully overlapping between passes and rejects. that's rarer than it sounds: most compression write-ups report only the cases that worked.

**what was missing, now closed or scoped:**
- no prior-art connection to LLM-as-judge reliability research — closed, see [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]]
- the fidelity gate's own non-determinism had no mitigation — partly closed: `--audit-sample` (multi-sample judge averaging, per Rating Roulette, arXiv:2510.27106) now exists in [[skills/note-compress/SKILL|note-compress]]
- still open: relinking (fragments individually true, reassembled into a false claim) is a named failure mode in the KBRA paper that neither the mechanical gate nor the new audit-sample catches — a submission should name this as a limitation, not silently omit it
- still open: single vault, single model (`openai/gpt-oss-20b` via Groq free tier) — a submission needs at minimum a second model run to show the negative result (density doesn't predict compressibility) isn't an artifact of one model's specific behavior

**venue:** [Workshop on Insights from Negative Results in NLP](https://insights-workshop.github.io/), co-located with EMNLP 2026, Budapest, Oct 22–29 2026. their stated scope explicitly wants ablations and "a technique doesn't generalize the way claimed" findings — the density-doesn't-predict result is exactly their target shape, and the venue carries no affiliation gate. mint a [Zenodo](https://about.zenodo.org/) DOI on the bench data (the tables already in the vault notes) alongside submission, so the numbers are citable independent of the workshop's own outcome.

**plan:**
1. re-run the density-predictor test (or the core benchmark) against a second model (Gemini Flash, already supported by the skill) — closes the single-model gap
2. write up the KBRA relinking gap as an explicit limitations section rather than leaving it undiscovered
3. draft as a short paper (workshop page limits are typically 4-8 pages) built directly from the four base notes above — the numbers and prose are already there, this is compilation and reframing for an academic audience, not new writing from scratch
4. submit to Insights from Negative Results in NLP; Zenodo-DOI the dataset/bench numbers in parallel, same week
5. arXiv cross-list only after the workshop gives a review trail — per current (Jan 2026) policy, an unaffiliated author needs a personal endorser, and a workshop acceptance gives an endorser something concrete to vouch for

## candidate 2: the readability/formatting synthesis, as a position piece

**base notes:** [[2026-08-30 readability and reading-speed research applied to note-taking vaults]], [[2026-08-30 agent reading versus human reading, which formatting rules transfer]], [[2026-09-01 why academic writing is hard to read]].

**why it's weaker as a paper:** this cluster is a well-sourced synthesis of others' findings (Nielsen Norman Group, Mayer, Cowan, Liu et al.'s "Lost in the Middle," the prompt-formatting study) plus one genuinely original piece of reasoning — the table distinguishing which human-reading rules transfer to an LLM reader and why (information-architecture rules transfer, perception/memory rules don't). synthesis with one original framing is a legitimate blog/position piece; it is not a novel empirical result, and an arXiv reviewer or workshop reviewer would read it as a survey, not a contribution.

**what's missing before it's more than a blog post:** an actual experiment. the human-vs-agent formatting table is currently argued from mechanism (saccades vs. attention weighting), not measured. the closest existing measurement is the prompt-formatting paper (arXiv:2411.10541) itself, which tested format types (markdown/JSON/plain) but not this vault's specific claims (bold-per-bullet doesn't help an LLM, chunk-size caps don't help an LLM). those two claims are cheap to test directly: hold a fixed retrieval or instruction-following task constant, vary only bold-density and list-chunking, measure task accuracy across a few model sizes. that would upgrade this from position piece to a real, small empirical contribution.

**venue:** publish as a blog post now, cross-post to [LessWrong](https://www.lesswrong.com/) or the [Alignment Forum](https://www.alignmentforum.org/) given the LLM-reading angle specifically — that community treats LLM-cognition-adjacent empirical posts as first-class and does not require arXiv or institutional affiliation. mint a Zenodo DOI on the final version for citability. skip arXiv for this one as written; thin case for an endorser to vouch for a synthesis piece.

**plan:**
1. run the cheap bold-density / chunk-size experiment above if the original framing is worth defending with data, otherwise publish as explicitly a position piece and say so
2. publish to a personal blog, cross-post to LessWrong/Alignment Forum
3. Zenodo-DOI the final version

## candidate 3: recency-proximity reranking, and its cross-domain confirmation

**base notes:** [[2026-08-31 recency-proximity reranking prior tested against real wikilinks]], [[2026-08-31 other candidate relatedness signals for search reranking]], [[2026-09-01 prior exposure as an implicit edge - the link between recency reranking and code-authorship expertise]], [[2026-09-01 research on expertise-location, federated privacy, and home-assistant LLM indexing]]. Surfaced during concurrent pkm-index work on this same vault today, not part of the original readability/compression thread — folded in here because it's the strongest single candidate of the three, on a fuller read.

**why it's the strongest of the three:** this is a full empirical study with a mechanistic proof, not just a benchmark table. three ways to fold time-closeness into search reranking were tested against real wikilinks as ground truth (multi-seed, full-sample, n=4,725): a global multiplier (rejected — every τ tested made ranking worse, -19.5% to -2.3% MRR), reciprocal rank fusion (rejected — never positive at any k, -21% to -4%), and a small additive term (validated — +7.73% to +8.60% MRR, positive on every seed tested). the rejection isn't just measured, it's *derived*: a rank-flip proof shows a multiplicative or rank-fused boost can demote a true target relative to any more-recent rival regardless of tuning, while an additive term can only break near-ties — and the vault measured the exact rival count (14.4 notes within 1 hour, 37.4 within 24 hours) that makes the multiplicative failure mode near-certain rather than occasional.

the companion note ([[2026-08-31 other candidate relatedness signals for search reranking]]) already does most of what candidate-3 originally listed as missing: it tests four more signals (Adamic-Adar, Jaccard, shared tags, session co-touch, Personalized PageRank, lift-normalized co-occurrence) across **four separate vaults**, not one — this vault plus three public Obsidian vaults (Obsidian's own help docs, and two named public vaults, `kepano` and `bramses`). it found a signal rejected on this vault (Adamic-Adar) flips to positive on a more densely-linked one, chased that down to link-graph density as the real variable (not personal-vs-curated authorship, which it explicitly ruled out by testing two more vaults) — and it caught and corrected its own earlier claim on a later adversarial pass (an opening "1.7% overlap, uniquely non-redundant" framing for co-commit didn't hold up under a consistent measurement, logged rather than quietly fixed). that self-correction, done in the open, is worth keeping in any writeup — it's evidence the negative results are real findings, not a first-draft that never got checked.

what makes it a paper rather than a vault note: a follow-up found the *same* mechanism, independently, in a completely different literature — [CodeCV](https://www.computer.org/csdl/proceedings-article/scam/2022/960900a143/1JSpk9oqpY4) (IEEE SCAM 2022) found first-authorship and recency of modification are the strongest predictors of who actually understands a piece of code, and this vault's own co-commit mining independently found the same additive-not-multiplicative shape (lift-normalization over raw co-edit weight, to stop hub files/committers from dominating). two unrelated domains, same failure mode, same fix — that generalization is the actual contribution, not just the reranking benchmark on its own.

**what's missing before it's submittable:**
- ~~single-corpus~~ already closed: four vaults tested, and the density-not-authorship explanation for why a signal's verdict flips between vaults is itself a real, generalizable finding worth stating as such in a writeup, not just a caveat
- the cross-domain claim (code-authorship expertise finding has the identical failure mode) is still argued from literature comparison, not tested directly — an actual replication of the rival-count dilution proof against a real git history (using CodeCV's own setup or a public repo) would make the generalization a measured result instead of an analogy
- the stacked multi-signal fusion (`&fusion=1`, additive combination of vector + recency + co-commit + Adamic-Adar) was calibrated against held-out data but the calibration itself used hand-inspected lambdas as a starting point before the grid search — worth stating the calibration procedure precisely in a writeup rather than summarizing it as "tuned"
- no comparison yet against a learned reranker (e.g. a small cross-encoder that has recency as a feature) as an upper-bound baseline

**venue:** four-vault validation plus a derived proof is enough to aim higher than the negative-results workshop as the first choice here — [ECIR](https://ecir2026.eu/)'s reproducibility/short-paper track or a [SIGIR](https://sigir.org/) short paper fits a validated positive result with this much cross-corpus evidence. [Insights from Negative Results in NLP](https://insights-workshop.github.io/) stays the fallback (still a real fit on the multiplicative/RRF rejections alone) if the IR-venue bar turns out too high without the missing cross-encoder baseline.

**plan:**
1. implement the small cross-encoder baseline comparison — the one piece of missing evidence for an IR-venue submission
2. write up the four-vault result, the density-explains-the-flip finding, and the cross-domain CodeCV confirmation as one paper; the self-correction episode is worth a short methods-note callout, not something to smooth over
3. submit to ECIR or SIGIR's short-paper track; fall back to Insights from Negative Results in NLP if reviews suggest the positive result needs more validation than a short paper allows
4. Zenodo-DOI the sweep data (the τ/λ tables, the four-vault comparison) regardless of venue outcome

## note on arXiv generally

as of the January 2026 policy change, an institutional email no longer auto-qualifies for endorsement — an unaffiliated author needs a specific personal endorser per category, found via each category's own "who can endorse" list. this is real friction, not a formality, and is the reason both plans above route through a workshop or a citable-but-unreviewed platform first rather than arXiv directly.

## related

- [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]] — the gap analysis this plan is built on
- [[2026-09-01 prior exposure as an implicit edge - the link between recency reranking and code-authorship expertise]] — candidate 3's cross-domain confirmation
- [[2026-08-31 recency-proximity reranking prior tested against real wikilinks]] — candidate 3's core experiment
- [[2026-09-01 process log - from readability question to publish plan]] — how this plan was reached
