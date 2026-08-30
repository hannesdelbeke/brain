---
tags:
- ai
- cli
- tools
aliases:
- free llm router
- llm rate limit fallback
- multi-provider llm fallback
---

> [!summary] eli5
> how to pool multiple free LLM providers behind a local router in CLI, automatically falling back when hitting 429 rate limits, and which tools manage keys, cooldowns, and error recovery.
> done: router mechanics, LiteLLM proxy fallback config, free provider comparison, and quick-start setup.
> **needs from you:** grab free keys from Google AI Studio and Groq, then run the local proxy.

## the problem

free tiers give strong inference, but strict rate limits (RPM, TPM, daily caps) kill agent loops mid-task. switching keys manually in terminal configs breaks flow.

a local router sits between your CLI tool and cloud providers:
- exposes a standard OpenAI-compatible endpoint (`http://localhost:4000/v1`)
- routes calls down a priority fallback chain
- catches `429 Too Many Requests`, puts that provider in cooldown (e.g. 60s), and instantly retries on the next free provider
- tracks request counts so you can see which providers hit ceilings

## router options

**LiteLLM proxy**: standard python daemon, connects 100+ backends, built-in fallback lists, RPM/TPM tracking, and cooldown timers. works with any agent supporting `OPENAI_BASE_URL` (like aider, opencode, cline).

**free-llm-gateway**: specialized proxy focusing on pooling free-tier keys, per-key rate limit dashboards, and automatic key rotation.

**tgpt**: zero-setup Go binary for terminal chat, automatically cycles public free web backends without needing API keys.

## free provider stack

combine these free tiers in your fallback chain:

- **Google AI Studio** (`gemini-2.5-flash` / `gemini-2.0-flash`): 15 requests/min, 1M tokens/min, 1500 req/day free. Highest capacity free tier.
- **Groq** (`llama-3.3-70b-versatile`): ultra-fast inference, generous free tier for open-weight models.
- **Cerebras**: fastest tokens/sec, free developer tier for Llama 3.3 70B.
- **OpenRouter** (`:free` models): routes to whichever free community endpoint is currently healthy.
- **Local Ollama**: terminal fallback at the end of the chain so tasks never fail even if all cloud quotas exhaust.

## LiteLLM fallback setup

create a config `~/.config/litellm/config.yaml`:

```yaml
model_list:
  - model_name: free-router
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: os.environ/GEMINI_API_KEY
  - model_name: free-router
    litellm_params:
      model: groq/llama-3.3-70b-versatile
      api_key: os.environ/GROQ_API_KEY
  - model_name: free-router
    litellm_params:
      model: cerebras/llama3.3-70b
      api_key: os.environ/CEREBRAS_API_KEY
  - model_name: free-router
    litellm_params:
      model: openrouter/google/gemini-2.0-flash-exp:free
      api_key: os.environ/OPENROUTER_API_KEY

router_settings:
  fallbacks: [{"free-router": ["free-router"]}]
  cooldown_time: 60
  num_retries: 3
```

start the proxy:

```bash
litellm --config ~/.config/litellm/config.yaml --port 4000
```

hook into any CLI agent:

```bash
export OPENAI_BASE_URL="http://localhost:4000/v1"
export OPENAI_API_KEY="sk-dummy"
```

**why:** [[free and low-cost CLI coding agents]]
