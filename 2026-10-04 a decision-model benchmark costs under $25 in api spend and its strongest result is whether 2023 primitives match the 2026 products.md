---
description: scoping an independent benchmark of 2026 decision models against autoregressive generation, costed and planned — api spend is single-digit dollars because jev bills $0.042 per million input and $0 output, clef-flash runs free inside cloudflare's 10,000 daily neurons, and every local arm has apache-2.0 weights, so a 4,000-decision pass across all six paid arms is $2.11 and a paper-scale run under $25; the novelty gap is not the mechanism, which arXiv:2501.17338 already covers, but the shipped systems and three unpublished questions — whether guidance's 2023 select() on the same base weights matches a 2026 product, whether vendor calibration survives independent ece, and whether confidence thresholds transfer between checkpoints, which llama.cpp's own post says they do not
---

> what does jev and it's lookalikes etc do. how do they defer. i dont have context. then could we write a paper on this? compare options etc. is it possible to do for free or are some options paid only. if so, how much would a barebones trail cost. and write up a plan on what we would test. what would be enough for a paper.

**needs from you:** decide whether to run this at all, and recommend yes but scoped to the three unpublished questions in the sections below rather than to a full landscape survey, because the landscape half is already owned by [arXiv:2501.17338](https://arxiv.org/abs/2501.17338) and the threshold-transferability half is owned by nobody. the one thing only you can supply is a decision on the labelled corpus: this plan assumes four public datasets, and if you would rather benchmark on your own already-labelled routing traffic that is a stronger paper and a private one, so it changes the venue as well as the method.

builds on [[2026-10-04 decision models package a three-year-old mechanism and the free route is llama.cpp's systemone endpoint]], which has the verified landscape, the licence traps and the eight claims that broke under checking.

## the api spend is not the constraint, and that reverses the usual reason not to run a benchmark

A decision model bills input tokens only, because the output is an index rather than a token stream, so the cost model that makes generative benchmarks expensive does not apply here.

Prices fetched from vendor pages on 2026-10-04, with the denominator stated so the arithmetic can be rechecked: **one pass is 4,000 decisions** (four datasets at 1,000 test items each) and input averages **800 tokens** per call, which is dominated by the option labels rather than the text, since [BANKING77](https://huggingface.co/datasets/mteb/banking77) carries 77 of them and [CLINC150](https://arxiv.org/abs/2207.13211) carries 150. That is **3.2M input tokens per arm per pass**.

| arm | published price | one pass | source |
|---|---|---|---|
| TypeSafe Jev 1.13 | $0.042 /M in, $0 out | **$0.13** | [genai-prices](https://raw.githubusercontent.com/pydantic/genai-prices/main/prices/providers/typesafe.yml), from docs.typesafe.ai |
| Fastino GLiNER2.5-Decide | $0.03 /M in, $0 out | **$0.10** | [docs.fastino.ai/pricing](https://docs.fastino.ai/pricing) |
| Fastino GLiDE | $0.15 /M in, $0 out | **$0.48** | same |
| Cloudflare Clef | $0.240 /M in | **$0.77** | [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) |
| Cloudflare Clef-flash | $0.090 /M in | **$0.29** | same |
| GPT-6 Luna, generative baseline | $0.10 /M in, $0.50 /M out | **$0.34** | OpenAI standard API |

**One full pass across every paid arm is $2.11.** Three repeats plus a pilot lands near $9, and a ten-times-larger run at 40,000 decisions lands near $21. Nothing in this project is gated on money.

Two prices are genuinely unavailable rather than merely unfetched. **Liquid AI's d1 publishes no per-token rate** — it is API-only with no downloadable weights, Liquid's own licensing for the LFM family is revenue-gated rather than metered, and the docs reference a `d1:free` identifier without rates. **OpenAI's Decisions API publishes nothing at all**, remaining in limited preview after its DevDay announcement on 2026-09-29, with no pricing page and no platform documentation. Both are omittable arms, and the plan below omits them rather than waiting on access.

## everything except jev can be run on free weights, so the free-only version of this paper is real

The question "can this be done for free" has a yes in it, with one $0.13 exception that is worth paying.

The **local arms are all Apache 2.0 or MIT**: Julia-1 at 144M, Laya at 421M, Kev-4B and lev served by `llama serve -hf ggml-org/<model>-GGUF` against `/v1/systemone`, [GLiNER2.5-Decide](https://huggingface.co/onnx-community/GLiNER2.5-Decide-ONNX) at 355M which answers on CPU and needs no GPU at all, and the reimplementations [SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev), [Kev](https://github.com/jaredpalmer/kev) and [jevlike](https://github.com/vinnylarouge/jevlike). **Exclude OpenJev-27B**, which is CC BY-NC 4.0 and the one licence that would taint a published result.

The **hosted arms have a free path too**: Cloudflare's 10,000 free neurons per day divide out to 0.458M input tokens daily for Clef and 1.222M for Clef-flash, so a full Clef pass is free spread over seven days and a Clef-flash pass over three.

What you cannot get free is **Jev itself**, which has no documented free tier — and Jev is the arm that matters most, because it is the calibration reference every open project measures itself against. At $0.13 a pass this is not a constraint, it is a rounding error, and a benchmark of this category that omits the category's reference implementation is not worth publishing.

So the honest answer on cost: **the barebones trial is $2 and the full paper is under $25 in API spend.** The real budget is GPU hours for the local arms and your own time building the harness, and if you have any consumer GPU the GPU hours are free as well.

## the novelty gap is the shipped systems, because one preprint already owns the mechanism question

This is the finding that should change the shape of the paper, and it came out of a prior-art sweep rather than out of the field's own materials.

**[Inferring from Logits: Exploring Best Practices for Decoding-Free Generative Candidate Selection](https://arxiv.org/abs/2501.17338)** (Ma et al., January 2025) already evaluates decoding-free logit scoring against standard token decoding, across five multiple-choice QA tasks and four clinical decision tasks, pairing several scoring estimators with foundation models of varying architecture and size. It is a preprint with no venue, which leaves room, but it means **"we compared logit readout to generation" is not a contribution any more** — that framing walks into a reviewer who knows this paper.

What does not exist, and what the sweep could not find in any form: **no published benchmark evaluates the shipped 2026 systems** — Jev, Clef, GLiNER2.5-Decide, the llama.cpp `systemone` set — and **no published work measures calibration for decision models specifically**, as distinct from calibration for ordinary LLM classifiers. Every calibration result in this field today is vendor-reported, and the single independent latency comparison that exists came out roughly 40x below the vendor headline.

Caveat on all of the above, and it is not a small one: these citations came back from a delegated search and **have not been opened and read**. Given that the parent note's own 17-source check broke eight claims, and that the pattern was attribution and numbers rather than mechanism, treat every arXiv ID here as a lead rather than a reference. **Read arXiv:2501.17338 in full before committing to a framing**, because it is the one paper that can invalidate the premise, and verify the rest at citation time.

## the strongest experiment is whether a 2023 primitive on the same base weights matches a 2026 product

If one experiment survives a budget cut, it is this one, because it tests a falsifiable claim about the entire product category and nobody can run it from vendor materials.

The parent note establishes that the mechanism is old: `select()` in Microsoft's **guidance** had bug reports against it by May 2023, [Outlines](https://arxiv.org/abs/2307.09702) followed in July 2023, [SGLang's `select`](https://arxiv.org/abs/2312.07104) in December 2023 with `token_length_normalized` as its documented default, and [GLiClass](https://github.com/knowledgator/gliclass) reached PyPI in June 2024, twenty-seven months before this wave. The vendors' implicit claim is that post-training buys something those primitives cannot deliver.

So hold the base weights fixed and vary only the method. Take an open base — Qwen3.5-4B is the natural choice, since both Kev-4B and SemIf use it — and run **guidance `select()`, Outlines `generate.choice`, and SGLang `select` against purpose-built Kev-4B on identical inputs**. If the 2023 primitives match on accuracy and calibration, the category is packaging and that is the paper's headline. If the post-trained model wins specifically on calibration while matching on accuracy, that is the paper's headline instead, and it is the first independent confirmation that the category does what it says.

Either outcome is publishable, which is the property a well-chosen experiment has and a badly-chosen one does not.

## calibration is the category's own claim, so measure it properly rather than reporting accuracy

Accuracy is not what these models sell. They sell a probability you can threshold on, and the literature on measuring that is mature enough that getting it wrong is an easy desk reject.

Report **ECE, adaptive ECE, Brier score, reliability diagrams, and risk-coverage curves with AURC**, not ECE alone. The reason is specific: ECE has documented pathologies — sensitivity to bin count, use of only the maximum probability rather than the full vector, no class-conditionality — and the metric you pick changes which recalibration method looks best, which means a single-metric calibration claim is unfalsifiable. [Guo et al., ICML 2017](https://arxiv.org/abs/1706.04599) is the foundational reference and temperature scaling the standard baseline; the binning critique and adaptive ECE come from [Nixon et al.](https://arxiv.org/abs/1904.01685). Risk-coverage matters here more than in a typical classification paper, because the operational use of a decision model is "act above threshold, escalate below it", which *is* selective prediction.

The reference point worth beating is in the open field already: [Laya's README](https://github.com/NandhaKishorM/laya) reports its fine-tuned checkpoint beating Jev on argmax accuracy, 0.766 against 0.727, while losing soft accuracy 0.471 to 0.580 and calibration with an ECE of 0.213 against 0.144 — and concedes the Jev figures are third-party and never measured there. An independent measurement of exactly that pair is a result on its own.

## threshold non-transferability is unpublished and is the most operationally useful thing to measure

This is the cheapest experiment in the plan and the one a practitioner would actually cite.

[llama.cpp's own launch post](https://huggingface.co/blog/ggml-org/decision-models-in-llamacpp) states that one vague support ticket "scored 0.25 with Julia-1 but 0.80 with Kev-4B". If that generalises, then **every confidence threshold in every deployment is checkpoint-specific**, a model swap silently changes the escalation rate, and nobody has quantified it. The same post notes that option *descriptions* carry real weight rather than being documentation — with bare labels Julia-1 routed "I was charged twice" to `shipping`, and adding descriptions "moved it to `billing` at 0.99".

So measure two sensitivities across all arms: **threshold drift**, by fixing a target precision on a dev split, reading off the threshold that achieves it per model, and reporting the spread; and **description sensitivity**, by running every dataset twice, once with bare class names and once with one-line descriptions, reporting the accuracy and calibration delta.

Both feed a third test the literature demands and the vendors ignore: **option-order and label bias**. Permute the option list per item and report accuracy variance under permutation, because logit scoring over option tokens is exactly the setting where surface-form competition and position bias bite, and a model that changes its answer when you reorder the list is not calibrated in any useful sense.

## the controls decide whether anyone believes the latency numbers, and this field has none of them

Every speed claim in this category is currently unbelievable, which is an opportunity rather than only a problem — careful measurement is itself the contribution.

**Never compare across a network boundary.** The one independent audit in the field found that CLM's 9x-to-13x figures compared local GPU execution near 28ms against trans-Pacific cloud round trips of 200-250ms, manufacturing an artificial multiplier out of geography. Hosted arms and local arms are therefore reported in separate tables and never ratioed against each other.

**Interleave arms and report ratios rather than absolutes**, because local CPU contention moves wall-clock enough to invert a result between runs, and a ratio measured within an interleaved block survives what an absolute measured in a block does not.

**Separate agreement from speed.** [SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev) is the model for this: it measures 1.023s against 5.332s, calls the comparison "a systems comparison rather than a claim that the two readouts are semantically equivalent", and discloses that the two methods **agreed on only 18 of 21 criteria**. A 5.21x speedup with three answers changed is a different result from a 5.21x speedup, so report the agreement rate beside every speedup and never collapse the two.

**Run a no-op control and a must-fail stub per arm.** A harness that reports plausible numbers for an arm that cannot possibly work is the failure that invalidates everything above it, so each arm needs a deliberately broken variant that the harness must score as broken, and a known-answer oracle it must score as correct, before any real number is reported.

**Use public labelled data rather than anything self-authored.** An eval set written alongside the thing it evaluates rewards paraphrase of its own prompt, and the whole point here is independence from the vendors' framing.

## what is enough for a paper, concretely

The bar is not novelty of mechanism, since that is taken. It is coverage, controls and released artefacts.

- **four or more public datasets**, none self-authored: BANKING77 and CLINC150 for many-class intent routing, [GoEmotions](https://huggingface.co/datasets/mteb/EmotionAnalysis) because it is still hard for zero-shot models, and [RAFT](https://arxiv.org/abs/2109.14076) for naturally-occurring tasks. CLINC150's out-of-scope split doubles as an abstention test, which is the one real-world behaviour the whole category needs and none of them advertise.
- **eight or more systems spanning all three architecture families** — decoder-with-masking, encoder-scorer, contrastive-cached — plus the three legacy primitives on fixed base weights and two autoregressive baselines, one open and one hosted.
- **calibration as a first-class result**, with the full metric set above and reliability diagrams, not accuracy with ECE appended.
- **released code and raw per-item predictions.** This is the part that makes it citable and the part the field conspicuously lacks: every number in circulation today is a summary statistic with no underlying predictions to re-analyse.
- **a negative-results section that survives contact with the data.** If the 2023 primitives match the 2026 models, say so; if vendor calibration holds up independently, say that instead.

On venue, the sweep suggests the NeurIPS Datasets and Benchmarks track is the natural home, with ICLR and EMNLP/ACL Findings as alternates, and an arXiv preprint plus a workshop paper as the realistic first move given the competing preprint is itself unpublished. Those deadlines and acceptance figures are **unverified** and want checking against each call for papers directly before anything is planned around them.

## what would sink this, named in advance

Three things, in descending order of likelihood.

**The premise collapses on a close reading of arXiv:2501.17338.** If that paper already covers the shipped systems or already reports calibration, the remaining contribution is threshold transferability alone — still a workshop paper, not a main-conference one. This is a one-afternoon check and it should happen before anything else in this plan.

**Access to the two closed arms never arrives.** Liquid d1 and OpenAI Decisions publish no prices and OpenAI's is in limited preview, so plan to omit both and say plainly that the paper covers the self-hostable and openly-priced subset of the category.

**The results are boring because everything is within noise.** Everything in this field answers inside 200ms and most of it is accurate enough on easy benchmarks, so a benchmark run only on solved datasets will show no separation. The defence is to put the hard cases in deliberately: many-class routing at 77 and 150 options, out-of-scope abstention, permuted option order, and the 255-option cap where the `choice` type is documented to refuse a 256th.
