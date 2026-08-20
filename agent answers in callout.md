---
tags:
  - ai
  - obsidian
  - pkm
---
Using [[Obsidian callouts|callouts]] to hold [[AI agent|agent]] responses inside an [[Obsidian note]].

## Trade-offs
- **Pros:** Clear boundary between human prompt and AI output; keeps notes compact like a collapsible FAQ.
- **Cons:** Prefixes (`> `) make editing, tables, and code fences tedious; reduces readability for long text blocks.

## Example
> How do I track prompt history?

> [!ai]- Response
> Store prompts in commit messages or external logs.

### Idea
to automate this in obsidian:

A background watcher detects questions in notes and appends generated answers inside collapsible callouts. This works like a [[Jupyter Notebook]] cell (prompt = code, callout = output).
### Related
- [[algo to differentiate between AI and human notes]] — Separating human prompts from generated text.
- [[human vs ai text context]] — Why human vs AI provenance matters.