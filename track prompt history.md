---
tags:
  - ai
  - git
  - pkm
---
How to preserve user prompt history and intent when using AI agents without cluttering note contents.

## The Prompt Retention Problem
When querying AI agents via CLI, Telegram bots, or mobile apps, the generated note is saved into the vault, but the original prompt is often lost. User prompts frequently carry the highest signal (user intent, specific constraints, edge cases).

## Approaches

**1. Commit Message Metadata (Recommended)**
Store the user prompt directly in the Git commit message body or trailer:
```git
add: note title

Prompt: "compare thinkpad x1 yoga gen 7 vs gen 8 used pricing"
```
- **Pros:** Zero visual clutter in Obsidian; fully queryable with `git log --grep`.
- **Cons:** Requires CLI wrapper or automation script.

**2. Callout Blocks**
Placing the prompt in a quote block above a collapsible agent response per [[agent answers in callout]]. Good for short Q&A, but adds visual friction to long documents.

**3. External Prompt Log**
A dedicated JSONL log or daily prompt history file that records every interaction timestamp, model name, and prompt string.

### Related
- [[algo to differentiate between AI and human notes]] — Separating human prompt lines from generated responses.
- [[human vs ai text context]] — Maintaining context between human intent and AI generation.
