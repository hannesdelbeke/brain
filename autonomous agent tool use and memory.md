---
tags:
  - ai
  - tools
  - architecture
  - agents
---
By default, AI agents don't have long-term memory. Asked to build a chart, they'll write it from scratch rather than searching past sessions.

Agents will autonomously reach for a session search tool when:
- **Debugging:** code fails and the agent searches past sessions for that specific error
- **Missing context:** you reference "a chart like the sleep one from last week" and it needs to look that up
- **Explicit rules:** `AGENTS.md` includes "always search past sessions when building [[Mermaid vs DataviewJS for Obsidian Charts|Dataview charts]]"

The interesting question isn't whether agents *can* search — it's whether making them *always* search is worth the cost.

## The latency trap

Enforcing "always search" via a tool rule is generally a net time loss.

**Cost:** 10–30s per request — Python script cold-boots, agent spends a model turn deciding to call it, reads results, evaluates relevance. For simple or novel tasks, this burns tokens for zero return.
**Benefit:** when tasks overlap past work, the agent skips 10+ minutes of trial-and-error by reusing proven code.

Blanket rules waste too much on basic tasks. Targeted rules or relying on the agent's heuristic to search only when stuck work better, but still carry the cold-boot penalty when triggered.

## Dropping below the decision threshold

The 10–30s cost has two components — script cold-boot and agent decision latency. Both are eliminable.

**Resident daemon:** keep the SQLite index and embedding model hot in RAM, dropping query time to 13-22ms measured. Built as HTTP rather than MCP, since every consumer can already speak it — [[lightning-fast unified search plugin for obsidian]]. Same architecture applied to session logs in [[cross-agent session indexing architecture]].

**Pre-prompt hook:** skip the agent deciding to search entirely. An [[how to inspect antigravity cli sessions|Antigravity]] hook intercepts the user's prompt, queries the warm MCP server, and injects the top matching past session into context before the agent starts reasoning. Zero round-trips.

This follows the [[Obsidian CLI + Agent Context at Scale|query, don't ingest]] principle — don't dump history into context, surface only what's relevant to the current prompt.

## When search is free, always-search wins

With MCP + hooks, the math flips:

**Cost:** near zero. <50ms latency, a few hundred tokens for the top match.
**Benefit:** the agent passively has relevant history on every prompt — reusing past code styles, workarounds, and solutions without deciding to search.

The 30-second penalty that made blanket rules wasteful disappears. The agent effectively gains long-term memory across sessions, approaching what dedicated systems like Codex's `memories_1.sqlite` or [[how hermes agent self improves|Hermes' three-tier memory]] provide, but grounded in actual execution history rather than curated summaries.
