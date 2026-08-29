---
tags:
- ai
- llm
- machine-learning
- overview
- benchmarks
aliases:
- popular llms
- top ai models
- frontier and local model landscape
---

Overview of current frontier cloud models and leading open-weight local LLMs across reasoning, coding, and lightweight tiers.

Related: [[how local AI models search the web and stay up to date]], [[model weights vs vector embeddings vs map-reduce]], [[Linux for AI and developer workflows]]

## Frontier cloud models

- **Anthropic Claude (Claude 3.7 / 3.5 Sonnet & Opus):** Industry benchmark for agentic software engineering, multi-step tool use, code refactoring, and nuanced instruction following.
- **OpenAI (GPT-4o, o1, o3-mini):** Leading multimodal vision/voice integration and dedicated test-time compute reasoning models (o-series) for complex mathematics and competitive programming.
- **Google Gemini (Gemini 2.0 / 3.7 Flash & Pro):** Massive 1M–2M token context windows, high inference throughput, low latency, and native multimodal understanding (audio, video, text).

## Open-weight & local models (Ollama / vLLM)

- **DeepSeek (DeepSeek-R1 & V3):** Breakthrough open-weight reasoning model using Mixture of Experts (MoE) and large-scale reinforcement learning, matching frontier reasoning performance.
- **Alibaba Qwen (Qwen 2.5 & Qwen 2.5 Coder):** Leading open-weight family for coding and mathematics in the 7B–32B parameter range. `qwen2.5:7b` is the standard sweet spot for local laptop execution.
- **Meta Llama (Llama 3.3 70B, Llama 3.1 8B, Llama 3.2 1B/3B):** Universal open-source baseline with broad ecosystem support. `llama3.2:3b` provides fast, low-memory edge inference.
- **Mistral (Mistral Small, Mistral Large 2, Codestral):** European open-weight pioneer focusing on compact efficiency, dense reasoning, and permissive enterprise licensing.

## Selection criteria

- **Agentic multi-file coding:** Claude 3.7 Sonnet, GPT-4o, DeepSeek-R1.
- **Massive context analysis (books, large repos):** Gemini 2.0 / 3.7 Flash & Pro.
- **Local laptop coding & Linux terminal help (16 GB RAM):** `qwen2.5:7b`, `llama3.1:8b`.
- **Fast edge / offline utility (< 4 GB RAM):** `llama3.2:3b`, `qwen2.5:3b`.
