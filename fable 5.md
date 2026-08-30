> [!summary] eli5
> anthropic's fable 5 leads SWE-bench as of august 2026 and does not appear on terminal-bench at all.
> done: records the benchmark position and the cache threshold it shares with opus 5.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** [[AI model comparison august 2026]]

## what it is

the model id is `claude-fable-5`. it leads SWE-bench verified at 95.0% against [[opus 4.8]]'s 88.6%, and SWE-bench pro at 80.3% against 69.2%. those are single-repository patch benchmarks, so the lead does not carry over to [terminal-bench 2.1](https://llmgateway.io/timeline), where [[GPT-5.6]] and [[opus 5]] hold the top two places and fable 5 does not appear.

two benchmarks, two different winners, is the whole reason to read [[AI model comparison august 2026]] rather than one leaderboard: SWE-bench measures a patch against one repository, terminal-bench measures long-horizon work in a shell, and a model can be built for one and not the other.

## cost behaviour

fable 5 shares opus 5's 512-token minimum cacheable prefix, the lowest tier, against 1024 for sonnet 5 and opus 4.8 and 4096 for opus 4.6 and haiku 4.5. a prefix under the threshold caches nothing and raises no error, verifiable only through `usage.cache_read_input_tokens`.
