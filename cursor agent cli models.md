---
tags:
- ai
- cli
- tools
- cursor
aliases:
- cursor agent models
- cursor-agent models
- cursor cli models
---

> [!summary] eli5
> `cursor-agent` exposes a long model list, but most ids are the same few families with effort and speed knobs. **auto** is the default: cursor router picks a model per request from task complexity, billed at that model's rate.
> done: how to list and switch models, what auto does, family strengths, when to pin a specific model.
> **needs from you:** nothing, default to auto unless you have a reason to pin.

> paid follow-up to [[free and low-cost CLI coding agents]], which only names cursor cli agent in passing.

## list and switch

```bash
cursor-agent models          # full list for this account
cursor-agent --list-models   # same, then exit
cursor-agent --model auto    # one-shot session with a pinned model
```

in an interactive session, `/model` opens the picker; `/model <filter>` jumps to a match. choice persists in `~/.cursor/cli-config.json`.

parameterized models accept bracket overrides on the cli, e.g. `--model 'claude-opus-4-8[context=1m,effort=high,fast=false]'`.

## what auto does

**auto** is cursor's router, not a single model. on each agent request a classifier reads task type and complexity, then routes to the cheapest model that should still give comparable quality.

you cannot pick which model handles a given turn under auto. you steer it with an optimization mode in the model picker:

| mode | behaviour |
|------|-----------|
| **cost** | previous auto logic; minimises token spend |
| **balance** | default for new users; trades intelligence, speed, and cost |
| **intelligence** | routes to more capable models on hard work; ~20–30% better on difficult tasks at higher spend |

billing is always at the **routed model's list price**. third-party routes also incur the cursor token rate on teams/enterprise plans.

the documented router pool targets [[GPT-5.6]], [[opus 5]], grok 4.5, and [[fable 5]]. grok 4.5 must stay enabled for the router to work — blocking it can disable auto entirely. on enterprise, blocked models are skipped and routing quality drops if too many are blocked.

for automation via the cursor sdk, auto is `auto-smart` with `optimize_for`: `cost`, `balanced`, or `intelligence`.

**when to use auto:** everyday agent work, when you do not want to think about model choice, when a specific model is region-blocked, or when you want spend to track difficulty automatically. pin a model when you need reproducibility, a known cost ceiling, or a specific strength (see below).

## decoding the model list

`cursor-agent models` prints ~200 ids. they are mostly variants of a small set of families plus effort and speed suffixes.

**effort tiers** (where the family supports them): `none` / `low` / `medium` / `high` / `xhigh` / `max`. higher effort → more reasoning, more tool calls, higher cost. **thinking** in the id (e.g. `claude-opus-5-thinking-high`) enables extended reasoning; use for architecture, debugging, and multi-step planning.

**fast suffix** (`-fast`): higher-priority inference, lower latency, usually ~2× token rate. composer fast is the product default for interactive speed.

**1m in display names**: 1 million token context window on that variant.

**no zdr** on [[fable 5]] ids: not zero-data-retention; enterprise retention rules differ from [[opus 5]].

## families and when to use them

two billing pools matter:

- **cursor models** (included usage on paid plans): grok 4.6, grok 4.5, composer 2.5
- **other models** (api-priced third-party): anthropic, openai, google, kimi, glm, etc.

### cursor models

| family | cli examples | reach for it when |
|--------|--------------|-------------------|
| **composer 2.5** | `composer-2.5`, `composer-2.5-fast` | default interactive coding; file edits, terminal, tight feedback loop; best speed/cost in the cursor pool |
| **grok 4.6** | `cursor-grok-4.6-high`, `cursor-grok-4.6-xhigh-fast` | hardest long-horizon agent tasks; multi-file refactors; when peak capability matters more than cost |
| **grok 4.5** | `cursor-grok-4.5-high-fast` | slightly older grok tier; still strong agent work; required for auto router |

composer has no effort knob — only standard vs fast. grok 4.6 supports `low` through `xhigh`; grok 4.5 tops out at `high`.

### anthropic

| family | cli examples | reach for it when |
|--------|--------------|-------------------|
| **claude opus 5** | `claude-opus-5-high`, `claude-opus-5-thinking-high` | complex multi-step agent work, deep planning, tool chains; see [[opus 5]] for cache and effort detail |
| **claude sonnet 5** | `claude-sonnet-5-high`, `claude-sonnet-5-thinking-high` | everyday coding at near-opus quality for less; good pinned default if auto feels too spendy |
| **claude fable 5** | `claude-fable-5-thinking-high` | peak coding quality where zdr is not required; see [[fable 5]] |
| **older opus/sonnet** | `claude-opus-4-8-high`, `claude-4.5-sonnet-thinking` | pin only when you need a specific older behaviour or benchmark position |

### openai

| family | cli examples | reach for it when |
|--------|--------------|-------------------|
| **gpt-5.3 codex** | `gpt-5.3-codex`, `gpt-5.3-codex-high` | agentic coding focused; strong terminal-bench class; cheaper than opus on many coding tasks |
| **gpt-5.6 sol** | `gpt-5.6-sol-high`, `gpt-5.6-sol-xhigh-fast` | hardest gpt work, long sessions; see [[GPT-5.6]] |
| **gpt-5.6 terra** | `gpt-5.6-terra-medium` | everyday agentic coding between luna and sol |
| **gpt-5.6 luna** | `gpt-5.6-luna-low-fast` | high-volume, latency-sensitive, or subagent fan-out |
| **gpt-5.4 / 5.2 / 5.1** | `gpt-5.4-high`, `gpt-5.2-fast` | pin when you want a specific generation's behaviour |

### google

| family | cli examples | reach for it when |
|--------|--------------|-------------------|
| **gemini 3.7 flash** | `gemini-3.7-flash-high` | cheap high-throughput agent work, large reads; see [[gemini 3.7 flash]] |
| **gemini 3.6 flash** | `gemini-3.6-flash-high` | prior flash generation; pin if 3.7 misbehaves on a task |
| **gemini 3.1 pro** | `gemini-3.1-pro` | heavier reasoning than flash tiers |

### other

| family | cli examples | reach for it when |
|--------|--------------|-------------------|
| **kimi k3 / k2.7** | `kimi-k3-max`, `kimi-k2.7-code` | code-oriented kimi tiers |
| **glm 5.2** | `glm-5.2-high`, `glm-5.2-max` | zhipu glm line; see [[GLM 5.2]] |

## practical picks

| situation | pick |
|-----------|------|
| default, unsure | `auto` (balance) |
| minimise spend | `auto` (cost) or `composer-2.5` |
| hard multi-hour agent run | `cursor-grok-4.6-xhigh` or `auto` (intelligence) |
| interactive edit loop | `composer-2.5-fast` |
| deep architecture / debugging | `claude-opus-5-thinking-high` or `gpt-5.6-sol-xhigh` |
| daily pinned model, good quality/cost | `claude-sonnet-5-high` or `gpt-5.3-codex` |
| bulk scripts, ci, many subagents | `gpt-5.6-luna-low-fast` or `gemini-3.7-flash-high` |
| need reproducible runs | pin explicit id with `--model`; auto will vary |

## related cli flags

- `--plan` / `--mode plan`: read-only planning, no edits
- `--mode ask`: read-only q&a
- `--print` (`-p`): non-interactive output for scripts; still has full tool access
- `--auto-review`: smart auto — server classifier auto-runs safe tool calls, prompts for the rest
- `--force` / `--yolo`: run shell commands without per-command approval

**why:** [[free and low-cost CLI coding agents]]
