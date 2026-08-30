> [!summary] eli5
> one table comparing the models that shipped or led a benchmark in august 2026, closed and open weights together, with a note per model behind each row.
> done as a snapshot of that month, and it dates fast, the whole table moved inside three weeks. it updates [[popular AI models landscape]], which still describes the 2025 generation.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** root

## the table

| model | vendor | weights | size and context | price per mtok | benchmark |
| --- | --- | --- | --- | --- | --- |
| [[GPT-5.6]] | openai | closed | sol, terra and luna variants | sol unchanged, terra cut 20%, luna cut 80% on 30 july | terminal-bench 2.1 89.5%, sol at xhigh, first |
| [[opus 5]] | anthropic | closed | 1M context | $5 / $25 | terminal-bench 2.1 89.1% at max, second |
| [[fable 5]] | anthropic | closed | 512-token cache prefix | not published | SWE-bench verified 95.0%, pro 80.3%, first |
| [[opus 4.8]] | anthropic | closed | 1024-token cache prefix | not published | SWE-bench verified 88.6%, pro 69.2% |
| [[gemini 3.7 flash]] | google | closed | 1M context, 64k max output | $0.75 / $3.75 to end of 2026 | not ranked |
| [[muse spark 1.2]] | meta | open, modified llama licence | 1M context | low-cost contributor tier | 82.9% terminal-bench claimed by meta, unverified |
| [[qwen3.8-max]] | alibaba | open | 2.4T total, 95B active, 1M context | self-hosted | not ranked |
| [[kimi K3]] | moonshot | open | ~2.8T total, active count unrecorded | self-hosted | not ranked |
| [[GLM 5.2]] | zhipu | open, MIT | 753B total, ~40B active | self-hosted | not ranked, reported as the reliable open agentic coder |
| [[GLM-5.3 flash]] | zhipu | unrecorded | unrecorded | unrecorded | unrecorded, released 26 august |
| [[OX Alpha]] | unattributed, 99% odds zhipu | unreleased | unrecorded | unrecorded | beat GPT-5.6 on coding benchmarks |

## the two benchmarks disagree

on [terminal-bench 2.1](https://llmgateway.io/timeline), which measures long-horizon agentic work in a shell, GPT-5.6 sol at xhigh leads at 89.5% and opus 5 at max follows at 89.1%, both unchanged across the second half of august. on SWE-bench, which measures single-repository patch correctness, fable 5 leads at 95.0% verified and 80.3% pro against opus 4.8's 88.6% and 69.2%, and does not appear on terminal-bench at all. the model that tops one is not the model that tops the other, so the choice follows the shape of the work rather than a single ranking.

## open weights closed the gap, licences did not

august 2026 was the month open weights stopped trailing. qwen3.8-max at 2.4T, kimi K3 at roughly 2.8T and GLM 5.2 at 753B all landed inside three weeks, with GLM-5.3 flash following on 26 august and muse spark 1.2 promised as open weights by meta ([release tracker](https://www.digitalapplied.com/blog/ai-model-releases-august-2026-tracker)). all of them are mixture-of-experts, so total parameters are the download size and active parameters are the compute per token, which is why qwen3.8-max at 95B active is a datacentre model that happens to be downloadable rather than a local one.

the licence decides whether any of them can ship. GLM 5.2's MIT grant attaches no conditions, where muse spark 1.2's modified llama community licence carries use restrictions, and that is the same split that governs open image models, where apache-2.0 weights are usable in a product and non-commercial ones are not however good they are.

## the benchmark table is not the cost comparison

in a long-running agent workload most of the bill is input-side, cache reads and cache writes rather than output, so per-token output price barely enters it and the model's minimum cacheable prefix matters more than its headline rate. an open-weight model self-hosted without a prompt cache can therefore cost more per unit of work than a rented one that caches, which is the comparison to run before switching rather than the table above.

the practical local target is none of the models here either. the mature 2026 local stack pairs ollama with a qwen3-class tool-calling model, explicitly not a think-mode one, with 12GB VRAM the floor to keep it resident.
