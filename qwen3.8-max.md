> [!summary] eli5
> alibaba's qwen3.8-max is a 2.4T parameter mixture-of-experts model, described on release in august 2026 as the largest open-weight model so far.
> done: records the specification and separates it from the smaller qwen models that are actually runnable locally.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** [[AI model comparison august 2026]]

## what it is

full release on 2 august 2026: 2.4T total parameters, 95B active, mixture-of-experts, 1M context, and the largest open-weight release to date at that point ([release tracker](https://www.digitalapplied.com/blog/ai-model-releases-august-2026-tracker)). [[kimi K3]] at roughly 2.8T passed it on total parameter count within the same month.

95B active of 2.4T is the number that matters for anyone thinking about running it. compute per token is mid-size, but the weights still have to be resident, so this is a datacentre model that happens to be downloadable rather than a local one.

## the qwen models worth running instead

the useful qwen releases are the small ones. qwen 3.6 35B runs in about 20GB and beats 120B models needing 70GB or more, which puts a capable agent on a single GPU. for a local voice or assistant stack the recommendation is a qwen3-class tool-calling model on ollama, explicitly not a think-mode variant, with 12GB VRAM the floor to keep it fully in VRAM.

the rest of the family shares the name and nothing else. [qwen-image-2512](https://huggingface.co/Qwen/Qwen-Image-2512) and [qwen-image-edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) are apache-2.0 diffusion models, and [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) is an embedding model at 70.7 MTEB-eng-v2, the best quality-per-size under 1GB. none of them share weights with qwen3.8-max.
