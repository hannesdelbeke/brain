---
tags:
  - ai
  - obsidian
  - pkm
---
Using [[Obsidian callouts|callouts]] to encapsulate [[AI agent|agent]] responses directly inside an [[Obsidian note]].

## Workflow
A simple background watcher observes [[git]] changes:
- You write a prompt or question inside a note.
- A local AI agent picks up the diff, generates a response, and inserts it directly beneath the question inside a collapsible callout.

This mirrors the execution flow of a [[Jupyter Notebook]] where the human prompt acts like the code cell and the agent callout acts like the output cell.

## Trade-offs

**Pros**
- Clear visual boundary between human intent and machine generation.
- Interactive FAQ feel with collapsible sections that keep the document compact.
- Easy to audit interactive human-bot dialogue history.

**Cons**
- Every line inside a callout requires a leading `>` prefix, which breaks standard multi-line editing and copy-pasting.
- Nested markdown elements (tables, code fences, child lists) become cumbersome to format inside blockquotes.
- Large callout blocks hurt long-form readability, making native markdown sections preferable for long text.

## Example Format

> How do I configure local git author trailers?

> [!ai]- Response
> Configure native trailers in `.gitconfig` or append `Co-authored-by:` to commit messages.

### Related
- [[algo to differentiate between AI and human notes]] — Differentiating human prompts from generated text.
- [[human vs ai text context]] — Why maintaining human vs AI provenance matters.