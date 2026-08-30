> [!summary] eli5
> anthropic's opus 5, the coding-agent model of august 2026, second on terminal-bench 2.1 and behind its own stablemate fable 5 on SWE-bench.
> done: collects the pricing, context, cache and effort behaviour in one place.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** [[AI model comparison august 2026]]

## what it is

the model id is `claude-opus-5`. it scores 89.1% at max effort on [terminal-bench 2.1](https://llmgateway.io/timeline), second to [[GPT-5.6]] sol at xhigh on 89.5%, and that gap did not move across the second half of august 2026. on SWE-bench it is behind [[fable 5]].

## cost behaviour

$5 per million input tokens and $25 per million output, a 1M context window, and a 512-token minimum cacheable prefix, the lowest of any anthropic model alongside fable 5. below that threshold nothing caches and no error is raised, which is the failure mode a thin agent prompt hits silently, visible only as a zero in `usage.cache_read_input_tokens`.

the `effort` parameter on `output_config` takes `low`, `medium`, `high`, `xhigh` and `max`, defaulting to `high`. lower effort means fewer and more consolidated tool calls, less preamble and terser output, and on opus 5 the low and medium tiers are strong enough to be the default for routine work, which makes it the cheapest change available per unit of saving. it is an adaptive-reasoning model, so `MAX_THINKING_TOKENS` is inert against it, and thinking cannot be disabled at xhigh or max, where a disable request returns a 400.

in a long-running agent workload the bill is dominated by cache reads and cache writes rather than output, so the 512-token prefix threshold is worth more attention than the headline $5/$25.
