> [!summary] eli5
> zhipu's GLM 5.2 is a 753B mixture-of-experts model released under MIT, reported in community threads as the most reliable open-weight model for agentic coding in august 2026.
> done: records the specification and the licence.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** [[AI model comparison august 2026]]

## what it is

753B total parameters with roughly 40B active, mixture-of-experts, MIT licensed. it followed [[qwen3.8-max]] in the same three-week release wave at a third the size, which is why it is the one people report actually running rather than the largest release of the month.

MIT is what separates it from the rest of the wave. [[muse spark 1.2]] ships under a modified llama community licence with use restrictions attached, where MIT attaches none, so GLM 5.2 is the frontier-scale open model of august 2026 with no licence question to answer before shipping on it.

## the family around it

[[GLM-5.3 flash]] landed on 26 august as the cheaper, faster member of the line. [[OX Alpha]], the unattributed model that beat [[GPT-5.6]] on coding benchmarks and reached production adoption within a day, was fingerprinted at 99% odds as an unreleased zhipu GLM-5.x flagship, so the family's real ceiling is probably above what 5.2 shows.

the caveat before self-hosting it is in [[AI model comparison august 2026]]: a model run without a prompt cache can cost more per unit of work than a rented one that caches, so the MIT grant removes the licence question and not the cost one.
