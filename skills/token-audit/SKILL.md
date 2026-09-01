---
name: token-audit
description: Measure where a claude code session spent tokens, by parsing the local jsonl transcripts
created: 2026-08-27
---

Scripts that read `~/.claude/projects/**/*.jsonl` and report real cost rather than guesses. What to do about the results is the `token-thrift` skill.

Every script takes the session to inspect on the command line, so nothing needs editing to point it at a different run.

[[session-cost.py]] ranks main sessions by base-input-equivalent cost, and prints turns, context per turn, cache creation share, cwd, and the tool result payload by tool. Pass `name=prefix` pairs to also total named session trees, or no arguments for the ranking alone.

[[subagent-cost.py]] does the same for the subagent transcripts under one session, taking the full session uuid, and prints the median first-call cache creation, which is the per-agent startup prefix write.

[[artifact-cost.py]] attributes each subagent's cost to the file it wrote, so a document or a module can be priced individually. Takes a session id prefix and the directory those files were written to. Splitting cost evenly across an agent's outputs overstates the cheap ones and understates the expensive, so read it as a ranking rather than an invoice.

[[web-cost.py]] finds where the WebFetch and WebSearch calls went, prints each agent's fetch count against its cost and what it wrote, and shows the opening line of its brief. That last column is the useful one — it is how a single instruction was traced to 122 fetches in one agent.

[[session-timing.py]] answers the wall-clock question rather than the cost one for a single session tree, taking its id prefix. It prints the span, summed agent runtime against union busy time so parallelism is a measurement rather than an impression, the histogram of time spent at N agents running, main-thread idle gaps at several thresholds, and the agent duration distribution.

Cost weighting is `cache_read * 0.1 + cache_creation * 1.25 + output * 5 + input`, in base input units, then `* 5 / 1e6` for dollars on the opus 5 rate. Change both numbers if the model or the ttl changes; a 1 hour ttl makes the cache creation multiplier 2 rather than 1.25.

Full corpus parse takes a few minutes on a 1.5 GB transcript directory, so run it in the background.
