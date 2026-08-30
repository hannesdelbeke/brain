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
> this note compares CLI AI coding agents you can reach for after a free quota runs out, gemini cli and codex both ran dry in the same week.
> done: six tools compared, agentic vs chat-only, free vs paid, with linux setup commands living in [[]] `free-ai-cli-notes.md` on the laptop rather than duplicated here.
> **needs from you:** nothing, recommend qwen code cli as the default pick for guided walkthrough tasks, free and agentic.

> ran out of gemini cli's free quota, then codex's free quota too, asked for a comparison of free alternatives and where cursor cli agent fits.

## the shape that matters

for a walkthrough task like "set up ollama on this laptop", the tool needs to run shell commands and read their output back, not just print instructions for you to copy-paste blind.
that splits the field into agentic CLIs and plain chat tools paired with a harness.

## free, agentic

- **qwen code cli**: alibaba's fork of [[Gemini CLI]], free via qwen oauth login, roughly 2000 requests/day, no api key needed. closest drop-in replacement for gemini cli's own workflow.
- **opencode** (`opencode.ai`): open-source harness, same agentic shape, works with any provider you point it at. quality depends entirely on which model you pick underneath, openrouter's `:free` models or a local ollama model both plug in.

## free, needs pairing for full guidance tasks

- **aider**: terminal pair-programmer, built for diff-based code edits rather than system setup. can run shell via `/run` but the flow is clunkier for a conversational walkthrough. pairs with openrouter free models or groq.
- **groq**: free api key, very fast inference on llama/kimi-class models, but plain chat only, no shell access on its own. only useful for this kind of task when driven through aider or opencode.

## fully local, free forever

- **ollama**: no quota, no api key, runs open-weight models on your own hardware, see [[popular AI models landscape]] for which model fits your ram/gpu. can't bootstrap its own install though, and once installed, local 7b-14b models read command output and adapt noticeably worse than the cloud free tiers above.

## not free

- **cursor cli agent** (`cursor-agent`): good agent quality, gpt-5/claude/gemini backends, but short trial credits then paid subscription, doesn't solve a quota problem, just moves the cost.
- **codex**: already ran out of its free quota, same problem this note exists to route around.

## recommendation

qwen code cli first, it's the only option here that's both free and fully agentic with no pairing needed.
opencode as the fallback if qwen's daily quota gets tight, since it can point at whatever free model still has headroom.

**why:** root
