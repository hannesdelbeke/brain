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

## note on arXiv generally

as of the January 2026 policy change, an institutional email no longer auto-qualifies for endorsement — an unaffiliated author needs a specific personal endorser per category, found via each category's own "who can endorse" list. this is real friction, not a formality, and is the reason both plans above route through a workshop or a citable-but-unreviewed platform first rather than arXiv directly.

## related

- [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]] — the gap analysis this plan is built on
- [[2026-09-01 process log - from readability question to publish plan]] — how this plan was reached
