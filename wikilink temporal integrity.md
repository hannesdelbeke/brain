---
tags:
  - technical
  - git
  - obsidian
  - pkm
---
Notes change constantly, but the reasons we link them don't. When you link to a note, you're referencing how it looked *right then*, not how it might look three years later.

### The Problem: Links Break as Notes Improve
Standard [[wikilink|wikilinks]] always point to the latest version of a note (`HEAD`). This creates subtle context bugs:

- **Day 1:** You write a note and link `[[Note B]]` as an example of a messy, unfinished draft.
- **Day 2:** You rewrite and polish `[[Note B]]`.
- **The bug:** The original note now points to a finished masterpiece, making your original reference look confused or wrong.

### The Idea: Resolve Links at the Date They Were Written
Instead of littering Markdown with ugly commit hashes (`[[Note B@abc1234]]`), keep standard clean wikilinks (`[[Note B]]`). Use Git in the background to figure out what the target note looked like when you actually wrote the link.

**Human reading**
- Clicking a link opens the current note as normal.
- If the target note changed since you made the link, Obsidian shows a subtle indicator (like a tiny clock icon `[[Note B 🕒]]` or hover note).
- Alt-clicking opens a diff showing how the note looked on the day you linked it.

**AI agents**
When an [[AI agent|AI agent]] reads an older note, it checks `git blame` to see when the link was created. If the linked note was heavily edited later, the agent reads the historical snapshot from that commit instead of hallucinating based on modern edits.

### Why This Beats Manual Hash Links
- **Zero extra typing:** You just write normal `[[notes]]`. No copying commit SHAs or custom anchors.
- **Clean Markdown:** If you switch editors in 10 years, your notes are standard plain text with no broken vendor syntax.
- **Active drift warning:** It warns you when a linked concept evolved, instead of silently going stale.

### References
- [[linking to git commits and diffs in obsidian via uri]] — Manual commit URIs (`[[note@sha]]`) that temporal integrity replaces.
- [[2026-07-31 historic obsidian links]] — Extracting historical graph edge birth/death timestamps from Git.
- [[how to keep history]] — Preserving Git timestamps required for temporal resolution when moving notes across submodules.
- [[agentic note taking]] — AI agents inspecting past revisions based on when a task was formulated.
- [[differentiate between AI and human notes]] — Distinguishing whether a historical link was created by a human or an AI agent.
- [[Obsidian plugin - Git]] — Underlying Git engine providing local logs and diff views for temporal resolution.



