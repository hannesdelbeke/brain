---
tags:
- ai
- cli
- tools
aliases:
- free ai cli
- cli coding agents
- gemini cli alternatives
---

> [!summary] eli5
> this note compares CLI AI coding agents you can reach for after a free quota runs out, gemini cli and codex both ran dry in the same week, with copy-paste linux setup commands for each.
> done: tools compared across agentic vs chat-only, free vs paid, and data-for-compute trade-offs, setup commands inline.
> **needs from you:** nothing, recommend opencode for zero-cost walkthrough tasks, or connect local ollama into qwen code.

> ran out of gemini cli's free quota, then codex's free quota too, asked for a comparison of free alternatives and where cursor cli agent fits.

## the shape that matters

for a walkthrough task like "set up ollama on this laptop", the tool needs to run shell commands and read their output back, not just print instructions for you to copy-paste blind.
that splits the field into agentic CLIs and plain chat tools paired with a harness.

## free, agentic

**qwen code cli**: alibaba's fork of [[Gemini CLI]]. the zero-key free browser oauth tier was discontinued on 2026-04-15; it now requires an alibaba modelstudio key (`sk-sp-...`), a third-party provider (e.g. openrouter), or a custom endpoint (local ollama).

```bash
npm install -g @qwen-code/qwen-code
qwen
```

first run launches `/auth` to choose alibaba modelstudio, a third-party provider key, or custom local endpoint. once connected, it works like gemini cli or claude code.

**opencode** (`opencode.ai`): open-source harness, same agentic shape, works with any provider you point it at. cleanest zero-cost agentic option since openrouter's `:free` models or a local ollama model plug in immediately with zero subscription fees.

```bash
curl -fsSL https://opencode.ai/install | bash
opencode auth login
```

pick a provider at the login prompt, openrouter with a `:free` model or ollama for fully local and zero cost.

## free, needs pairing for full guidance tasks

**aider**: terminal pair-programmer, built for diff-based code edits rather than system setup. can run shell via `/run` but the flow is clunkier for a conversational walkthrough. pairs with openrouter free models or groq.

```bash
python3 -m pip install aider-chat
export OPENROUTER_API_KEY=sk-or-...   # openrouter.ai, free signup
aider --model openrouter/deepseek/deepseek-chat-v3.1:free
```

swap the model string for any other `:free` model at openrouter.ai/models?max_price=0.

**groq**: free api key, very fast inference on llama/kimi-class models, but plain chat only, no shell access on its own. only useful for this kind of task when driven through aider or opencode.

```bash
python3 -m pip install aider-chat
export GROQ_API_KEY=gsk_...   # console.groq.com, free signup
aider --model groq/llama-3.3-70b-versatile
```

## fully local, free forever

**ollama**: no quota, no api key, runs open-weight models on your own hardware, see [[popular AI models landscape]] for which model fits your ram/gpu. can't bootstrap its own install though, and once installed, local 7b-14b models read command output and adapt noticeably worse than the cloud free tiers above.

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
ollama run qwen2.5-coder:7b
```

needs a decent gpu, or patience on cpu, for 7b+ models. to drive it from aider or opencode instead of the raw chat:

```bash
export OLLAMA_API_BASE=http://127.0.0.1:11434
aider --model ollama/qwen2.5-coder:7b
```

## data-for-compute trade-offs

some providers drop fees or slash token rates by feeding prompts, code snippets, and repo context back into model training:

- [[muse spark 1.2]] (muse code): meta's terminal agent offers a discounted contributor tier. token rates drop in exchange for letting meta log repo context, subagent spawns, and steer traces.
- google ai studio (`gemini-2.5-flash` / `gemini-2.0-pro`): generous free api quotas (15 req/min, 1M tokens/min), but free-tier prompt data and human reviews feed future model training. attaching paid gcp billing stops data logging.
- openrouter (`:free` models): community-hosted `:free` endpoints frequently harvest prompt logs for open-weights distillation and benchmarking.
- codeium (windsurf / cli): free individual tier logs code context and completions for model training, while team plans guarantee zero data retention.

trade-off: high token headroom for open-source work and personal scratchpads, but keep them off private vaults and client repos.

## not free

**cursor cli agent** (`cursor-agent`): good agent quality, gpt-5/claude/gemini backends, but short trial credits then paid subscription, doesn't solve a quota problem, just moves the cost. model picker and when-to-use guidance in [[cursor agent cli models]].

```bash
curl https://cursor.com/install -fsS | bash
cursor-agent
```

login via browser on first run, worth it only if paying is fine.

**codex**: already ran out of its free quota, same problem this note exists to route around.

## recommendation

opencode first for zero setup costs, pointing at openrouter's `:free` models or local ollama.
qwen code cli if you already have an alibaba cloud modelstudio key or want to drive local ollama via qwen's agentic loop.
for automatic fallback across multiple free keys on rate limits, use a local proxy like [[free LLM router and rate limit fallback]].

**why:** root
