---
name: the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism
description: the vault's two-pass compression research (classify-and-cut, then adversarially score) independently reinvented LLM-as-judge; that literature names and fixes the exact non-determinism the vault observed live
created: 2026-09-01
tags:
  - pkm
  - ai
  - compression
  - research
  - llm-as-judge
---

> critically work through what's missing in the compression research, find related papers, see it from a new angle

[[2026-08-31 classifier-based compression with an adversarial fidelity gate|the two-pass compression method]] — one agent cuts, a second independent agent scores what survived — was arrived at from first principles in this vault, with no reference to prior art on using an LLM to grade another LLM's output. That prior art exists, is substantial, and directly explains a failure this vault already measured live: [[2026-09-01 note-compress skill - design, adversarial review, and bench data|the same prompt, on the same note, passing the gate once and mangling a fenced code block the next]].

## the gap

grading an LLM's output with a second LLM call is a named technique, **LLM-as-judge**, and it has a known reliability problem. [Zheng et al. 2023, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"](https://arxiv.org/abs/2306.05685) (NeurIPS 2023) found position bias (a judge favors whichever answer it sees first — only GPT-4 stayed consistent across position-swaps more than 60% of the time) and verbosity bias (weaker judge models fail a padded-repeat attack over 90% of the time). Their fix: call the judge twice with the two answers swapped, only count a verdict as real if both calls agree.

more directly on point, ["Rating Roulette: Self-Inconsistency in LLM-As-A-Judge Frameworks"](https://arxiv.org/html/2510.27106v1) (2025) measured a judge scoring the *same input twice* and found intra-rater agreement (Krippendorff's alpha) as low as 0.265–0.563 across repeat runs — "LLM raters are extremely volatile." this is exactly the vault's own observation, restated as a general, already-quantified property of the method rather than a one-off surprise. their fix, and the finding that matters most here: **run the judge multiple times and average the scores** — not majority vote, and not forcing temperature=0, which the paper found actually hurts agreement with human judgment compared to sampling normally and averaging.

[Liu et al. 2023, "G-Eval"](https://arxiv.org/abs/2303.16634) (EMNLP 2023) reaches a compatible answer by a different mechanical route: instead of one greedy score, read the score token's log-probabilities and take the probability-weighted expectation across the distribution — smooths the same single-sample noise for free, in one call, but requires the API to expose token log-probabilities for an arbitrary score token, which Groq and Gemini don't cleanly offer. multi-sample averaging gets a similar effect without needing that access.

## a second gap: verification at the compression boundary is its own active research line

two 2025 papers frame LLM-driven compression itself as an attack surface, not just a lossy pipe. ["CompressionAttack"](https://arxiv.org/html/2510.22963v2) shows a compression module isn't safety-tuned the way the model reading its output is, so adversarial input can survive compression undetected, and a weaker downstream reader is hurt worst. the KBRA paper, ["Safe to Check, Unsafe to Use: Relinking at the Compression Boundary of LLM Agents"](https://arxiv.org/html/2606.21732), names a failure distinct from ordinary unfaithfulness: **relinking** — fragments that were each individually true in the original get reassembled by the compressor into a new claim the original never made. eleven existing defenses missed this failure mode entirely. the vault's own mechanical gate (subset-check on wikilinks, dates, numbers, code spans) cannot catch relinking either — it only proves nothing was *deleted*, never that nothing was *recombined* into a new, false claim. this is a real, currently unaddressed gap in the shipped skill, distinct from the framing-drift gap the audit-sample addition (below) targets.

## a negative result that turned out to be uncatalogued

the vault's live-corpus test found link density (0.04 to 4.02 wikilinks per 100 words) and number density predict nothing about whether a note compresses safely — pass and reject notes fully overlap on both metrics. a literature search for this exact question — does a cheap textual signal predict compressibility — came back empty. the closest adjacent work is Chain-of-Density's entity-density *target* for good summaries (~0.15 entities/token) and formal compressibility theory (Verma & Lee), neither of which tests density as a *predictor* and rejects it. the vault's finding reads as a genuine small negative result, not a rediscovery — worth stating plainly rather than hedging, per [[2026-09-01 why academic writing is hard to read|the vault's own writing-quality research]] on stating a real finding instead of manufacturing false uncertainty around it.

## what changed as a result

[[skills/note-compress/SKILL|note-compress]]'s default pipeline is unchanged — one compression call plus the free mechanical gate is still the right default, per the vault's own break-even math. what's new is an opt-in `--audit-sample` pass: for a sample of notes that already passed the mechanical gate, run the framing-fidelity judge 3 times per note and average, instead of trusting a single judge call the way the original two-pass design did. this doesn't fix relinking (still open, see above) but it does directly address the one failure mode this vault caught live and previously had no way to monitor.

## related

- [[2026-08-31 classifier-based compression with an adversarial fidelity gate]] — the method this note supplies prior art and a reliability fix for
- [[2026-09-01 note-compress skill - design, adversarial review, and bench data]] — where the non-determinism was first observed, unexplained, in a fenced-code stress test
- [[2026-09-01 publish plan - readability and compression research as papers]] — where this gap analysis feeds into a submittable empirical study
