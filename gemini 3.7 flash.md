> [!summary] eli5
> google's gemini 3.7 flash is the cheap agentic-coding tier of august 2026, 1M context at $0.75 per million input tokens, promotional through the end of the year.
> done: records the specification, the pricing and the output ceiling.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** [[AI model comparison august 2026]]

## what it is

announced on [the google blog](https://blog.google) and aimed at agentic coding and document processing: 1M context, 64k maximum output, and $0.75 input and $3.75 output per million tokens through the end of 2026. that is 15% of [[opus 5]]'s $5/$25 on the same context window, which puts it in the slot haiku occupies in the anthropic line, the model bulk work routes to once quality has been checked rather than assumed.

the 64k output ceiling is the constraint worth noticing. a 1M-context model that emits at most 64k in one response is built for reading large inputs, not for writing large outputs, so a task that generates a whole file tree still needs chunking.

## where it sits in the line

gemini 3.5 flash is the default model in [[antigravity]] 2.0, google's terminal agent, having beaten gemini 3.1 pro on terminal-bench 2.1 at 76.2%. 3.7 flash is the next step in the same line, so the agent that runs on it inherits the price drop rather than needing a different tool.
