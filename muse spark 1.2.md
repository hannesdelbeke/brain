> [!summary] eli5
> meta's muse spark 1.2 is the model behind the muse code agent, and meta said in august 2026 that its weights go open under a modified llama community licence.
> done: records the specification, the claimed benchmark and the licence caveat.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** [[AI model comparison august 2026]]

## what it is

muse spark 1.2 pairs with [muse code](https://techcrunch.com/2026/08/05/meta-launches-muse-code-an-ai-agent-for-large-code-bases/), the terminal agent meta shipped in beta on 5 august 2026 for large repositories, and it is the model that agent runs on. the specification is 1M context, context compaction, async parallel tool calls and whole-repository training, with persistent subagents for long-horizon work and a claimed 82.9% on terminal-bench 2.1. that claim is meta's own and the model does not appear on the [leaderboard](https://llmgateway.io/timeline) alongside [[GPT-5.6]] and [[opus 5]], so it is unverified rather than a third place.

whole-repository training is the differentiator worth watching. background agents accumulate context instead of starting fresh, and a local event log replays after a crash so every subagent spawn, tool call and steer is recoverable, which is a different bet from the stateless-session model most terminal agents take.

## the licence

meta said the 1.2 weights go open under a modified llama community licence. modified means it is not an open-source licence in the sense [[GLM 5.2]]'s MIT grant is, and the restrictions land on exactly the commercial use a shipping product needs. the same distinction already decides which open image models are usable, where apache-2.0 weights can ship and non-commercial ones cannot however good they are. read the licence before the benchmark.

muse code itself is positioned on price, a one-line install and a low-cost contributor tier, which is where it competes rather than on capability.
