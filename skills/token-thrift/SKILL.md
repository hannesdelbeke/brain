---
name: token-thrift
description: Cut the cost of an agent session or an agentic app — what to change, in order of effect
created: 2026-08-27
---

A run costs `api_calls * price_per_call`. There are two levers, fewer calls and less context per call, and nothing else. The bill is mostly input-side: cache reads and cache writes are around three quarters of it, so fewer turns save a lot. Output is the remaining quarter and rising with heavy thinking use, measured at 7% in mid-2026 and 23% by August, so check it rather than assuming it is noise.

A tool result of `n` tokens costs `n * (1.25 + 0.1 * remaining_turns)` — 2.25x face value with 10 turns left, 11x with 100. When something enters context matters more than how big it is.

## Do these, in this order

1. **Batch independent tool calls.** Three reads in one block is one turn, not three. Serialise only when a call's input depends on a previous result. This is the biggest lever by a wide margin.
2. **One session per task.** Price per call scales with carried context — the same work costs roughly 4x more at 400k than at 100k. Clear between unrelated tasks.
3. **Put standing context in the agent definition or skill, not in a `Read`.** Anything every agent needs — stack, conventions, router table — belongs in a system prompt that caches once, not in a file re-read per agent.
4. **Name files in the brief and forbid the repo-wide search.** Say which files may be touched, say to stop and ask rather than grep, and ask for a one-line summary instead of narration.
5. **One gate command, and inject its output.** Collapse every check variant into one script. A skill can run it before its text reaches the model, making the opening survey cost zero tool calls.
6. **Redirect long output to a file, read the decisive lines.** Test runs, build logs, traces. The file stays on disk for the next question, the context window does not.
7. **Route models by whether a wrong answer is caught arithmetically.** With a hard gate — types, tests, an audit script — a cheaper model is safe for editing work. Orchestration stays on the top model. Never switch mid-session: caches are model-scoped and a switch discards them. Hand cheap work to a subagent instead.
8. **No image unless a number will not do.** Assert on measured pixels, screenshot on failure only.
9. **Scope tools and MCP servers per repo.** An agent with a tool in reach will use it. List only what the work needs; the rest should be absent, not discouraged.
10. **Cap web fetches per agent, and require a file.** Research that returns as a string dies at the next compact and gets paid for twice. Anything expensive to find gets written to disk before the agent returns.
11. **Background slow work; use the 1 hour cache TTL when waits are inherent.** A gap past five minutes expires the cache, and the next call rewrites the prefix at 1.25x instead of reading it at 0.1x.
12. **Pick a reasoning effort tier once per conversation.** Lower tiers issue fewer, more consolidated tool calls and shorter output, which now hits both sides of the bill. Never change it mid-session — the resolved value renders into the prompt and invalidates the cache.

## Where mutable state goes

Render order is `tools`, `system`, `messages`, and a cache breakpoint caches everything before it. Anything that changes per turn goes at the tail of `messages`, appended to the newest user turn, never into `system`. Fifty tokens of state in the wrong place rewrites the whole prefix every call, at 12.5x the price of reading it.

Silent cache invalidators, all the same bug: a timestamp or uuid or session id early in the prompt, unsorted dict serialisation, iteration over a set, conditional prompt sections, per-user tool sets, a model or effort change. Zero cache reads on a prefix that should be identical means one of these.

A prefix below the model's minimum cacheable length caches nothing and raises no error. The threshold is 512 to 4096 tokens depending on model and is not monotonic across generations, so check it rather than assuming. Verify with `usage.cache_read_input_tokens`; `usage.input_tokens` is the uncached remainder only.

## Do not bother

Each of these has been measured and is noise: MCP tool schemas when tool search defers them, subagent spawn overhead, splitting long agents into short ones, single large file reads, idle cache expiry on a busy run, and thinking tokens.

## Budgeting a project

Count the work, do not scale a previous invoice. Enumerate the writes, add the unavoidable reads, add one gate run per unit of work, divide by the batch factor you intend to hold, multiply by the per-call price at your intended context size. The gap between that number and what a comparable run actually cost is the size of the batching and redundant-read problem.

Measure before believing any of this about a specific run — intuition about where tokens go is wrong more often than it is right. Frame results as cost per completed task rather than total spend, since total spend rises with adoption, and remember that a failed cheap run is not a saving.
