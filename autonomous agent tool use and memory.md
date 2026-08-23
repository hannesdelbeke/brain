autonomous agent tool use and memory

by default, ai agents operate fast and confidently. if asked to build a chart, they will usually write it from scratch rather than searching past sessions.

they will autonomously use a session search tool when:
- debugging: if code fails, the agent searches past sessions to see if it solved that specific error before.
- missing context: if you ask for "a chart like the sleep one from last week", it realizes it lacks context and searches for it.
- explicit rules: if AGENTS.md includes a rule to "always search past sessions before writing new scripts".

time balance of "always search" rules:
enforcing an "always search" rule is generally a net time loss.

cost: every request incurs 10-30 seconds of latency to run the search, read results, and evaluate them. for simple or novel tasks, this burns tokens and time for no return.
benefit: when tasks overlap with past work, the agent skips 10+ minutes of trial-and-error by reusing proven code.

balance: a blanket rule wastes too much time on basic tasks. a better approach is targeted rules (e.g. "always search past sessions when building dataview charts") or relying on the agent's natural instinct to search only when it hits a wall or missing context.
