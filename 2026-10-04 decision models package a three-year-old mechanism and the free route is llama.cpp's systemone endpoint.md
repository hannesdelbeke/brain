---
description: eight decision models shipped in the 19 days after typesafe's jev on 2026-09-15, but the mechanism — one forward pass, read only the allowed options' logits, softmax — is documented in gliner (nov 2023) and sglang's select primitive (dec 2023), so the genuinely new parts are calibration and a shared wire format; the free route is llama.cpp's /v1/systemone endpoint serving julia-1 at 144m/3ms or gliner2.5-decide at 340m on cpu with no gpu, and every speed figure in circulation is vendor-reported with clm-8b's 9x already challenged as a cache artefact
---

> this online article. write a dated note for it, then explain it plainly, and say when to use what. we only care about the free options, or tell me how to make a duplicate of e.g. jev. also are there other existing things like jev? afaik there was a open source thing similar for over a year. [followed by a pasted article comparing five decision models]

**needs from you:** decide whether a routing, triage or gating step in your own stack is worth moving off a chat model, recommend running `llama serve -hf ggml-org/Julia-1-GGUF` against fifty of your own already-labelled examples before adopting anything, because every latency and accuracy figure published so far is vendor-reported and the only number that decides this is accuracy on your data.

## a decision model returns one option from a closed list with a probability, and never writes text

The call carries a **state** (a message, a page, an agent's situation) and a set of typed questions whose answers are fixed in advance, and the response is the winning option plus a probability for each one. The downstream code branches on that result directly, so there is no JSON to parse, no retry on malformed output and nothing to hallucinate — [TypeSafe's own docs](https://jevapi.dev/) call it "a smart if statement".

Three question types have become the de facto standard across every implementation: **choice** picks one of up to 255 options, **score** rates against an ordered rubric and returns an expected level that can fall between two rungs, and **noul** answers a yes/no question with the probability of yes.

The reason it is fast is structural rather than a matter of model size. An autoregressive model emits one token at a time and each token waits on the one before it, so latency scales with how much it writes; a decision model runs a single forward pass over the input, reads the logits at the final position for the tokens that spell the allowed options, and softmaxes those. Output length is zero by construction, which is why [Jev bills output tokens at $0](https://pydantic.dev/docs/ai/models/typesafe/) — there is no output stream to charge for.

## the mechanism predates jev by nearly three years, which answers the "open source thing for over a year" question

The thing being remembered is almost certainly the [GLiNER](https://arxiv.org/abs/2311.08526) lineage, and it is older than a year rather than younger. GLiNER landed as arXiv 2311.08526 in November 2023 and went on to NAACL 2024, introducing exactly the pattern now being sold as new: a bidirectional encoder that takes labels specified at inference time, scores them against the text in one parallel pass rather than one pass per label, and beats prompted LLMs at zero-shot while being a fraction of the size.

[GLiClass](https://github.com/knowledgator/gliclass) is the direct adaptation of that architecture from entity tagging to whole-sequence classification, concatenating runtime labels with the input behind `<<LABEL>>` and `<<SEP>>` tokens and reading them all in one forward pass. Throughput drops only 7-20% going from 1 label to 128, which is the same sub-linear scaling the 2026 decision models advertise, and the labels are a plain Python list passed at call time with no retraining. The straight line from there to today is explicit in the naming: [Fastino's GLiNER2.5-Decide](https://www.marktechpost.com/2026/09/24/fastino-releases-gliner2-5-decide-a-340m-open-weight-decision-model-that-runs-on-cpu/) is fine-tuned from `gliner2-large-v1` on the same DeBERTa-v3-large encoder.

The second strand of prior art is the inference-stack primitive, and it is equally old. [SGLang's `select`](https://lmsysorg.mintlify.app/docs/references/frontend/choices_methods) shipped with the SGLang paper in December 2023 and is described in its own docs as computing the normalized log probabilities of every choice and returning the highest, with `token_length_normalized` as the default and `unconditional_likelihood_normalized` available for the debiased version. `outlines.generate.choice` and `guidance`'s `select()` cover the same ground from the constrained-decoding side, and the much older [zero-shot classification pipeline](https://github.com/urchade/GLiNER) over an NLI model has been the boring answer to runtime-defined labels since 2020.

So the honest framing is that **nobody invented a new mechanism in September 2026**. What arrived is a product category: calibrated probabilities as the contract rather than an afterthought, a shared wire format several vendors agreed on, and small models post-trained specifically for the task instead of a general model being coaxed into it.

## the field is eight models in nineteen days, not the five the article counts

The article's table stops at Jev, CLM-8B, OpenAI's Decisions API, Clef and Strands Decider, which misses three entrants and the one release that matters most for running this free.

Shipped closed or API-only: **Jev** on 2026-09-15 from TypeSafe AI at $0.042 per million input tokens, **OpenAI's Decisions API** on 2026-09-29 at DevDay on a specialised GPT-6 Luna, **Liquid AI's d1** on the same day as `d1:free` on the Liquid API with [no downloadable weights at all](https://docs.liquid.ai/lfm/models/complete-library), and **Fastino's GLiDE**, a "thinking" decision model that spends extra compute only when the choice is uncertain.

Shipped with open weights: **CLM-8B** on 2026-09-23 from Stanford and NVIDIA under Apache 2.0, **GLiNER2.5-Decide** on 2026-09-24 from Fastino at 340M under Apache 2.0, and **Clef** plus **Clef-flash** and **Strands Decider 2B** all on 2026-10-01, Apache 2.0 across the board.

Then on 2026-10-02 the capability [landed in llama.cpp upstream](https://huggingface.co/blog/ggml-org/decision-models-in-llamacpp), which is the event that turns this from a procurement question into a `brew`-and-go question.

## the free route is llama.cpp's /v1/systemone endpoint, and it is two commands

`llama.cpp` now implements the same System One format Jev introduced, so the free path is not a reimplementation you maintain but a base URL you change.

```sh
llama serve -hf ggml-org/Julia-1-GGUF      # 144M, 3ms
llama serve -hf ggml-org/Kev-4B-GGUF:Q8_0  # 4B, 12ms, pick a quant
llama serve                                # router mode, loads on demand
```

Then `POST http://localhost:8080/v1/systemone` with `state`, `questions` and optionally `images`, and the response carries `answers` keyed by your question names with `probabilities`, `confidence`, and a `usage` block reporting zero output tokens. Five models are wired up, with medians measured on one RTX PRO 6000: Julia-1 at 144M and 3ms, Laya at 421M and 5ms, Kev-4B at 12ms, lev at 4B and 36ms, and OpenJev at 27B and 43ms with vision. The first four are Apache 2.0; **OpenJev is CC BY-NC 4.0, so it is not free for commercial use** and is the one licence trap in the set.

Two operational details from that post are worth more than the latency table. Option descriptions carry real weight rather than being documentation — Julia-1 misrouted a double-charge complaint on bare labels and hit `billing` at 0.99 once descriptions were added. And confidence thresholds do not transfer between models, since the same vague ticket scored 0.25 on Julia-1 and 0.80 on Kev-4B, so a threshold tuned on one checkpoint is meaningless on another.

## if you want no gpu at all, gliner2.5-decide is the one that answers on cpu

[GLiNER2.5-Decide](https://huggingface.co/onnx-community/GLiNER2.5-Decide-ONNX) is 340M parameters, Apache 2.0, non-generative, needs no prompt template, and answers in 167ms on a 48-core CPU. It takes a schema of typed questions and returns each answer with a probability distribution, a confidence score and constraint-feasibility metadata, and it is documented for air-gapped use. For anyone whose blocker is "I have no GPU and the data cannot leave", this is the shortest path in the entire landscape, and it is also the most direct descendant of the 2023 prior art above.

## duplicating jev yourself is about twenty lines, and several people have published theirs

The whole trick is masking: build a prompt holding the state, the question and the option labels, run one forward pass, take the logits at the final position, keep only the positions corresponding to each option's token, and softmax those into a distribution. [SemIf](https://github.com/TheoLeeCJ/SemIf) calls this decision-native scoring and measures it at 5.21x against generating the same JSON — 1.023 seconds versus 5.332 for 21 binary criteria on a frozen Qwen3.5-4B on an RTX 3090 — and its shared mode prefills the state once into a KV cache, replicates that cache across branches, and evaluates every criterion's option positions in one batched pass.

If you would rather start from someone else's code than write it, the clones differ mainly in backbone and ambition: [SemIf](https://github.com/TheoLeeCJ/SemIf) is MIT on Qwen3.5-4B and the most careful about measurement, [Kev](https://github.com/jaredpalmer/kev) is a trainable family on Qwen3.5/3.8 that serves TypeSafe's own SDK unmodified, [jevlike](https://github.com/vinnylarouge/jevlike) is MIT and deliberately pedagogical with both a from-scratch byte-level encoder and a frozen pretrained path, [von](https://github.com/wfzyx/von) is a 395M ModernBERT encoder served on CPU, and [dejavu](https://github.com/Kanaricc/dejavu) does it with vLLM and no training at all.

What none of them replicate is the part that is actually hard. The interface is a weekend; the calibration — probabilities that mean what they say across domains — is what the post-training buys, and TypeSafe has published neither its architecture nor its data. [Laya's own README](https://github.com/NandhaKishorM/laya) is the most honest statement of this in the whole field: its base checkpoints sit at or below baseline on typed decisions and only the fine-tune reaches 0.766 against Jev's published 0.727, so it bills itself as a fast base to specialise rather than a zero-shot engine.

## pick by the constraint that actually binds you, because latency almost never does

| the binding constraint | pick | why this one |
|---|---|---|
| no GPU, data cannot leave | GLiNER2.5-Decide, 340M, Apache 2.0 | 167ms on CPU, air-gap documented, no prompt template |
| fastest local, English text | Julia-1, 144M, via llama.cpp | 3ms median, Apache 2.0, one command to serve |
| accuracy with a consumer GPU | Kev-4B or Clef-flash 9B | 12ms in llama.cpp; Clef-flash claims a 38.8ms median |
| images in the state | hosted Clef, or OpenJev locally | the only two with a vision encoder, and OpenJev's CC BY-NC bars commercial use |
| agent action selection, fixed action set | CLM-8B, Apache 2.0, 75MB head | caches action vectors, so a revisited state drops from 1.7ms to 0.6ms |
| replacing existing Jev calls | anything speaking `/v1/systemone` | llama.cpp, Clef, kev-onnx and CLM's client all accept the same request |

The question that decides it is rarely speed. Everything in that table answers inside 200ms, which is below the point where a human or an agent loop notices, so the real discriminators are whether the data can leave your machine, whether the licence permits your use, and whether the thing is actually right on your examples. A wrong answer in 3ms is worse than a right one in 500ms, and the article's own closing point is the correct one.

## every speed figure in circulation is vendor-reported, and clm-8b's has already been challenged

The article says it found no independent benchmarks, which was true of the quality numbers and is no longer quite true of the speed ones. CLM-8B's headline 9x over Jev has been [independently characterised as a cache artefact](https://zenn.dev/null_teck/articles/clm-vs-decision-models): the 4x-13x figures assume 100% vector cache hits against a fixed action set and are compared to cloud API round trips, where cold inference with dynamic options must push every candidate through Qwen3-8B and lands past 500ms. Jev also scored higher than CLM on tool calling and WikiRacing in CLM's own tests.

Fastino's numbers need the same discount applied twice over. It chose both the benchmark and the opponents, and its Fast Decisions comparison runs against **JevK5, an open reproduction, rather than TypeSafe's Jev** — so "GLiDE 64.81 against Jev 57.91" is a sanity check that a small model is in the game, not a ranking.

The Jev baseline itself is unstable across sources, which is the clearest single sign that none of this has been independently measured: TypeSafe publishes 70 to 500ms, Cloudflare measures a 524ms median for the same service in its own comparison, and the two cannot both be describing the same workload.

## three smaller corrections to the article

Clef's Qwen identifier is **not** a typo, which the article flags as suspicious and worth checking. [Cloudflare's launch post](https://blog.cloudflare.com/clef-decision-models/) post-trains Clef from Qwen3.8-27B and Clef-flash from Qwen3.5-9B, froze both backbones, and jointly optimised a routing head alongside rank-256 LoRA adapters. The article also misses that Clef carries a vision encoder accepting up to four images, takes 64 questions per request on a 64K context, and that while the weights are Apache 2.0 the hosted service is $0.24 and $0.09 per million input tokens rather than free.

Jev launched on 2026-09-15 rather than the 16th, and CLM-8B on 2026-09-23 rather than "late September", which matters only because the compressed timeline is the article's own framing.

Strands Decider's median is reported as 115ms on an RTX 3090 in [its repository](https://github.com/strands-labs/strands-decider) against the 106ms the article quotes, and the repo adds the detail that explains the architecture: it takes a Qwen3.5-2B-Base decoder torso, discards the language-modelling head entirely, and replaces it with a ~1M-parameter pointer head adapted by a rank-16 LoRA. That is the same move Clef, Laya and CLM all make — keep a frozen general backbone, bolt on a tiny trained head, and never generate a token.
