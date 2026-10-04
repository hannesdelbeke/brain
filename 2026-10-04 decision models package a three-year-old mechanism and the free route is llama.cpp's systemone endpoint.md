---
description: eight decision models shipped in the 19 days after typesafe's jev on 2026-09-15, but the mechanism — one forward pass, read only the allowed options' logits, softmax — shipped in guidance in may 2023 and gliclass on pypi in june 2024, so the new parts are calibration and a shared wire format; the free route is llama.cpp's /v1/systemone endpoint serving julia-1 at 144m/3ms or gliner2.5-decide at 355m on cpu, and a 17-source check on 2026-10-04 broke 9 widely-repeated facts including strands decider's aws attribution, clef's $0.24 price and jev's 193x headline, which independent testing puts near 5x
---

> this online article. write a dated note for it, then explain it plainly, and say when to use what. we only care about the free options, or tell me how to make a duplicate of e.g. jev. also are there other existing things like jev? afaik there was a open source thing similar for over a year. [followed by a pasted article comparing five decision models] — then: subagent research each link or thing mentioned in separate subagent. see if it exists. is not hallucinated. and quoted or described correctly.

**needs from you:** decide whether a routing, triage or gating step in your own stack is worth moving off a chat model, recommend running `llama serve -hf ggml-org/Kev-4B-GGUF` against fifty of your own already-labelled examples before adopting anything, because the one independent latency comparison in this whole field came out roughly 40x below the vendor headline.

## a decision model returns one option from a closed list with a probability, and never writes text

The call carries a **state** (a message, a page, an agent's situation) and a set of typed questions whose answers are fixed in advance, and the response is the winning option plus a probability for each. The downstream code branches on that result directly, so there is no JSON to parse, no retry on malformed output and nothing to hallucinate — TypeSafe's [own documentation](https://docs.typesafe.ai) calls Jev "a smart if statement or a smart switch statement … an intelligence-infused logic gate".

Three question types have become the de facto standard across every implementation: **choice** picks one of up to 255 options (a 256th returns a 400), **score** rates against an ordered rubric and returns an expected level that can fall between two rungs, and **noul** answers a yes/no question with the probability of yes.

The reason it is fast is structural rather than a matter of model size. An autoregressive model emits one token at a time and each token waits on the one before it, so latency scales with how much it writes; a decision model runs a single forward pass over the input, reads the logits at the final position for the tokens that spell the allowed options, and softmaxes those. Output length is zero by construction, which is why [Jev bills output tokens at $0](https://pydantic.dev/docs/ai/models/typesafe/) — there is no output stream to charge for.

## the mechanism shipped in may 2023, which answers the "open source thing for over a year" question

The pattern is three and a half years old, not one, and it arrived in three independent places before anyone called it a product category.

The earliest shipped form is `select()` in Microsoft's **guidance**, which has bug reports and fixes against it from May 2023. **Outlines** followed with choice-constrained generation in July 2023, backed by [Efficient Guided Generation for Large Language Models](https://arxiv.org/abs/2307.09702) and on PyPI that August. [SGLang's `select`](https://lmsysorg.mintlify.app/docs/references/frontend/choices_methods) arrived with its [December 2023 paper](https://arxiv.org/abs/2312.07104) and is documented in exactly the terms the 2026 launches use: `token_length_normalized` is the default and "selects the option with the highest average logprob across all of its tokens". SGLang's own contribution was batching and KV-cache sharing, not the primitive — its paper notes that "vLLM lacks a 'select' primitive" and that "Guidance, although offering a 'select' feature, is limited to a batch size of 1".

The encoder strand is the closer architectural ancestor and is nearly as old. [GLiNER](https://arxiv.org/abs/2311.08526) was submitted 14 November 2023 and published at NAACL 2024, introducing labels supplied at inference time, scored against the text in one parallel pass, "an advantage over the slow sequential token generation of LLMs". [GLiClass](https://github.com/knowledgator/gliclass) adapts that architecture from entity tagging to whole-sequence classification, concatenating runtime labels behind `<<LABEL>>` and `<<SEP>>` tokens, and **reached PyPI as 0.1.0 on 2 June 2024** — 27 months before this wave. Its paper measures the scaling that the 2026 launches advertise: throughput falls only "7–20% from 1 to 128 labels" (section 4), against cross-encoders that need a forward pass per pair, for "roughly 2.3×–16× higher average throughput" (section 3, tables 6 and 7).

The line to today is explicit in the naming rather than inferred: [Fastino's GLiNER2.5-Decide](https://fastino.ai/models) is fine-tuned from `gliner2-large-v1` on the same DeBERTa-v3-large encoder.

So **nobody invented a mechanism in September 2026**. What arrived is a product category: calibration as the contract rather than an afterthought, a wire format several vendors agreed on, and small models post-trained for the task instead of a general model coaxed into it.

## the free route is llama.cpp's /v1/systemone endpoint, and it is one command

`llama.cpp` [implemented the System One format on 2 October 2026](https://huggingface.co/blog/ggml-org/decision-models-in-llamacpp), so the free path is not a reimplementation you maintain but a base URL you change.

```sh
llama serve -hf ggml-org/Kev-4B-GGUF        # the quick start
llama serve -hf ggml-org/Julia-1-GGUF       # 144M, 3ms
llama serve -hf ggml-org/Kev-4B-GGUF:Q8_0   # pick a quantization
llama serve                                 # router mode, loads on demand
```

Then `POST http://localhost:8080/v1/systemone` with `state`, `questions` and optionally `images`, and the response carries `answers` keyed by your question names with `probabilities`, `confidence`, and `"usage": {"input_tokens": 130, "output_tokens": 0}`. Five models are wired up, with medians on a single RTX PRO 6000: Julia-1 at 144M and 3ms, Laya at 421M and 5ms, Kev-4B at 12ms, lev at 4B and 36ms, and OpenJev at 27B and 43ms with vision. The first four are Apache 2.0; **this OpenJev is CC BY-NC 4.0, so it is not free for commercial use** and is the one licence trap in the set.

Two operational details from that post are worth more than the latency table. Option descriptions carry real weight rather than being documentation — with bare labels Julia-1 sent "I was charged twice" to `shipping`, and adding descriptions "moved it to `billing` at 0.99". And confidence thresholds do not transfer between models: one vague ticket "scored 0.25 with Julia-1 but 0.80 with Kev-4B", so a threshold tuned on one checkpoint is meaningless on another.

## if you want no gpu at all, gliner2.5-decide is the one that answers on cpu

[GLiNER2.5-Decide](https://huggingface.co/onnx-community/GLiNER2.5-Decide-ONNX) is **355M** parameters on Fastino's own figure, Apache 2.0, and answers with a p50 of 167ms on a 48-vCPU Xeon 8581C at batch size 1 with 64 tokens of input. Fastino documents that "it runs locally on CPUs and can be deployed in air-gapped environments", which makes it the shortest path for anyone whose blocker is no GPU plus data that cannot leave.

It is an encoder scorer with "no autoregressive decoding", but it is not prompt-free: callers must reproduce an exact sequence layout of `[P]`, `[L]`, `[SEP_STRUCT]` and `[SEP_TEXT]` tokens, so a client library is close to mandatory.

## duplicating jev yourself is about twenty lines, and the published clones measure it honestly

The whole trick is masking: build a prompt holding the state, the question and the option labels, run one forward pass, take the logits at the final position, keep only the positions corresponding to each option's token, and softmax those. [SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev) calls this decision-native scoring, where "one forward pass reads declared option logits; no answer token is sampled", and measures 1.023s against 5.332s for 21 binary criteria on a frozen Qwen3.5-4B on an RTX 3090 — the generative baseline "took 5.21× as long as direct readout".

That repo is also the model for how to report such a number, because it refuses to let the ratio stand as a quality claim: it calls the comparison "a systems comparison rather than a claim that the two readouts are semantically equivalent", and discloses that the two methods **agreed on only 18 of the 21 criteria**. A 5.21x speedup with three answers changed is a different result from a 5.21x speedup.

If you would rather start from published code, the options differ mainly in backbone and maturity. [SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev) is MIT on Qwen3.5-4B and the most careful about measurement, [Kev](https://github.com/jaredpalmer/kev) is Apache 2.0 with checkpoints from 0.8B to 27B and runs TypeSafe's own Python SDK unchanged, and [jevlike](https://github.com/vinnylarouge/jevlike) is MIT and deliberately a "research starter, not a product clone", offering both a from-scratch byte encoder and a frozen pretrained path. [von](https://github.com/wfzyx/von) (395M ModernBERT, OpenVINO on CPU) and [dejavu](https://github.com/Kanaricc/dejavu) (vLLM, no training at all) are real but early — dejavu is two commits.

What none of them replicate is calibration, and TypeSafe has disclosed more of its method than the clone READMEs imply: no architecture, weights or paper, but it states the model is transformer-based and trained solely on synthetic data via Reinforcement Learning for Calibrated Decisions. [Laya's README](https://github.com/NandhaKishorM/laya) names the same RLCD acronym for its own training, so the open projects are reimplementing a stated method rather than guessing at a black box.

## laya's readme is the most honest document in the field, and it cuts against its own headline

[Laya](https://github.com/NandhaKishorM/laya) (Apache 2.0, Convai Innovations) states plainly that "the base checkpoints sit below the majority-class baseline (0.362 and 0.352 against 0.461)" and that "all of the capability on this benchmark comes from fine-tuning", concluding "Laya is a fast base to specialise, not a zero-shot decision engine".

Its fine-tuned checkpoint does beat Jev on argmax accuracy, 0.766 against 0.727. The same README then concedes the part that matters more for this use case: Jev wins **soft accuracy 0.580 to 0.471 and calibration, ECE 0.144 against Laya's 0.213**, and notes the Jev figures are "third-party published, never measured here". Since calibration is the thing the post-training is supposed to buy, a model that wins argmax and loses calibration has not overtaken Jev at its own job.

The Apple Silicon port is real and its figures hold: [laya-mlx](https://github.com/mizorewww/laya-mlx) measures a 13.4ms median for a short English decision and 7.4ms on the multilingual checkpoint, peaking at 943.6 and 687.6 MiB, "both under 1 GiB".

## pick by the constraint that actually binds you, because latency almost never does

| the binding constraint | pick | why this one |
|---|---|---|
| no GPU, data cannot leave | GLiNER2.5-Decide, 355M, Apache 2.0 | 167ms p50 on CPU, air-gap documented |
| fastest local, English text | Julia-1, 144M, via llama.cpp | 3ms median, Apache 2.0, one command to serve |
| accuracy with a consumer GPU | Kev-4B or Clef-flash 9B | 12ms in llama.cpp; Clef-flash's own median is 38.8ms |
| images in the state | hosted Clef, or OpenJev locally | the only two with a vision encoder, and OpenJev's CC BY-NC bars commercial use |
| agent action selection, fixed action set | CLM-8B, Apache 2.0, 75MB head | caches action vectors, so a revisited state drops from 1.7ms to 0.6ms |
| replacing existing Jev calls | anything speaking `/v1/systemone` | llama.cpp, Clef, kev-onnx and CLM's client all accept the same request |

The question that decides it is rarely speed. Everything in that table answers inside 200ms, below the point where a human or an agent loop notices, so the real discriminators are whether the data can leave your machine, whether the licence permits your use, and whether the thing is right on your examples. A wrong answer in 3ms is worse than a right one in 500ms.

## a 17-source check broke nine facts that circulate as settled

Every figure in this note was checked against primary sources on 2026-10-04, one source per check. Nine claims that appear across published coverage did not survive, and the pattern in them is worth more than the individual corrections: **the failures cluster in corporate attribution and in vendor speed multipliers, not in technical mechanism.** Every architectural claim checked out; almost every number with a company's name attached to it moved.

- **Strands Decider is not an AWS product.** `strands-labs` is an independent GitHub org created 2026-09-29, publishing as `StrandsAgents` on Hugging Face, with no AWS or Amazon ownership claim anywhere. AWS appears only as training infrastructure, a `p5.48xlarge` instance. Its own figures are 1.9B parameters, a 115ms median on an RTX 3090 and 153ms on an M3 **Pro**, and the 106ms quoted in coverage appears nowhere.
- **Jev's 193.6x and 444.6x are upper bounds the vendor concedes as such**, measured by its own model-capabilities team. Independent testing puts Jev near **5x faster and 8.6x cheaper** than Mistral Small 4 — roughly 40x below the headline. So "there are no independent benchmarks" is also wrong; there is one, and it is the most useful number in the field.
- **Clef's $0.24 per million input tokens is not published anywhere** by Cloudflare — not the blog, the changelog or the developer docs. Only Clef-flash's $0.09 is documented.
- **CLM-8B's own pages name no institutional affiliation.** The "Stanford and NVIDIA" framing is press attribution; the repo lists authors (Kwok, Kang, Suresh, Saad-Falcon, Pavone, Ré, Mirhoseini) and a release date of 2026-09-19.
- **CLM's model card gives Jev no verifier score.** The 71.1% and 83.1% figures in circulation are not on it; it says only that Jev scores "below pass@1" on those long-horizon tasks, and it concedes no task where Jev wins.

The remaining four are smaller but the same shape. `jevapi.dev`, widely cited as if authoritative, states that it "is not affiliated with or endorsed by TypeSafe AI". **JevK5 is not a reproduction of Jev** — it is an independently trained Apache-2.0 alternative on open Qwen weights, "not Jev's unpublished model architecture", which matters because Fastino's Fast Decisions table benchmarks against JevK5 (57.6%) rather than TypeSafe's Jev while reporting itself at 60.2%. OpenAI's widely-quoted "150ms versus 1.6s" for its [Decisions API](https://community.openai.com/t/devday-2026-announcements-and-developer-resources/1402006) traces to no OpenAI source, as does the "specialized version" framing — OpenAI says only "powered by GPT-6 Luna", the product remains in limited preview with no platform documentation. And the reported Hugging Face takedown of refusal-stripped GLM-5.3 did not happen: those variants are still live, one with 85,887 downloads last month.

## clm-8b's speedup is conditional rather than fake, which is the distinction vendor and critic both blur

An [independent benchmark](https://zenn.dev/null_teck/articles/clm-vs-decision-models) published 2026-09-25 found that CLM's 9x to 13x figures compare local GPU execution at roughly 28ms against trans-Pacific cloud round trips of 200 to 250ms, which "creates an artificial ~9× multiplier", and that they assume disaggregated vector caching at a 100% hit rate where varied or dynamic action sets give a hit rate of "exactly 0%". On a miss, full 8B forward passes are required and multi-action batches "scale past 500 ms".

The same author also measured genuine cached gains, 7x on one task and 115.6ms against Kev-4B's 235.6ms, and recommends CLM for fixed-action real-time control. So the speedup is real under its stated assumptions and absent without them, which makes "cache artefact" too strong and the vendor's unqualified "up to 9x" too generous. The usable rule is that CLM pays off exactly when your action set is fixed and revisited, and not otherwise.

## three names each refer to more than one project, so check before you clone

**OpenJev** is three things: the 27B CC BY-NC model in llama.cpp, the former name of [SemIf](https://github.com/TheoLeeCJ/SemIf-OpenJev), and [GPT-AGI/OpenJev](https://github.com/GPT-AGI/OpenJev), an MIT Phase-0 alpha on Qwen2.5-0.5B. The non-commercial warning applies only to the first.

**lev** is llama.cpp's 4B model on Qwen3.5-4B, and separately [franckverrot/lev](https://github.com/franckverrot/lev), a one-commit 350M experiment on LFM2.5 that its author calls a "fun weekend experiment".

**SemIf** is both the decision engine above and a 144-decision eval suite used in [Kev's benchmark table](https://github.com/jaredpalmer/kev) (Jev 0.965, Kev 0.917), a collision neither project's docs acknowledge. Separately, [kyegomez/open-jev](https://github.com/kyegomez/open-jev) is a non-functional architecture demo with random weights by design, so it is not a starting point despite the name.

## the article this came from was right about the mechanism and wrong about the field

Its technical account is sound — the single forward pass, the closed option set, the zero output tokens, the warning to measure accuracy on your own data rather than trust declared times. Its Clef detail is better than its own hedging suggested: it flagged the Qwen version identifier as a possible typo, and Cloudflare really does say "By freezing Qwen3.8-27B for Clef and Qwen3.5-9B for Clef-flash".

Where it goes wrong is the landscape. It counts five models where eight shipped in nineteen days, missing Fastino's GLiNER2.5-Decide and GLiDE and Liquid's [d1](https://docs.liquid.ai/lfm/models/complete-library) (API-only, listed as `| d1 | API | — | — | — | No |`, so there is nothing to self-host). It misses llama.cpp's upstream support entirely, which is the one release that changes what a reader can do today. It repeats the AWS attribution for Strands Decider and the Hugging Face takedown, neither of which holds. And its claim that Laya "scores lower than Jev on nearly every test" is contradicted by Laya's own argmax numbers, though it lands nearer the truth than Laya's headline does once calibration is included.
