autonomous agent tool use and memory

by default, ai agents operate fast and confidently. if asked to build a chart, they will usually write it from scratch rather than searching past sessions.

they will autonomously use a session search tool when:
- debugging: if code fails, the agent searches past sessions to see if it solved that specific error before.
- missing context: if you ask for "a chart like the sleep one from last week", it realizes it lacks context and searches for it.
- explicit rules: if `AGENTS.md` includes a rule to "always search past sessions before writing new scripts".

## time balance of manual tool rules
enforcing an "always search" rule via an agent tool is generally a net time loss.

cost: every request incurs 10-30 seconds of latency to run the search, read results, and evaluate them. for simple or novel tasks, this burns tokens and time for no return.
benefit: when tasks overlap with past work, the agent skips 10+ minutes of trial-and-error by reusing proven code.

balance: a blanket rule wastes too much time on basic tasks. a better approach is targeted rules (e.g. "always search past sessions when building dataview charts") or relying on the agent's natural instinct to search only when it hits a wall.

## optimizing search to <1 second
the 10-30s delay comes from the python script cold-booting and the agent spending a turn deciding to call the tool. to drop this under 1 second:
1. mcp server: keeps the sqlite db and embedding models hot in ram, dropping execution time to <50ms.
2. pre-prompt hook: instead of forcing the agent to decide to use a tool, an antigravity hook intercepts the user's prompt, hits the mcp server instantly, and injects the top past session into the context before the agent even sees it. zero round-trips.

## time balance of MCP + hooks
if the search is optimized via mcp + hooks, the math flips entirely:

cost: near zero. injecting a past snippet adds almost no latency (<50ms) and minimal token overhead.
benefit: the agent passively has your entire history as context without needing to "decide" to search.

balance: when search is this fast, an "always search" background hook becomes a massive net win. the agent will seamlessly reuse past code styles and solutions on every prompt without the 30-second penalty.
