---
tags:
  - technical
  - git
  - obsidian
  - pkm
---
How temporal integrity solves context drift across evolving notes by resolving target note states at the time a link was written, without cluttering Markdown with manual commit hashes.

### Core Problem
Traditional [[wikilinks|wikilinks]] are living pointers that always resolve to `HEAD` (the latest note state).

- **Day 1:** Note A references `[[Note B]]` as an example of a messy draft.
- **Day 2:** You rewrite and polish `[[Note B]]`.
- **Result:** Note A now points to a clean note, breaking the original context and making the reference nonsensical.

Temporal integrity preserves standard clean wikilink syntax (`[[Note B]]`), but uses Git history to resolve the target note's state at the moment the link was committed.

### Authoring UX
- **Pure Markdown:** Type standard wikilinks (`[[Note B]]`) without looking up commit SHAs or inserting anchors.
- **Clean text:** Notes remain portable and readable across all Markdown editors.

### Reading & Navigation UX
- **Default click:** Navigates to the live `HEAD` version of the note.
- **Visual drift badge:** Displays a subtle indicator (e.g. `[[Note B 🕒]]` or underline) if the target note has changed since link creation.
- **Hover preview:** Displays a header notice: *"Target note modified 3 times since this link was created (View snapshot at Link Date)"*.
- **Alt + Click:** Opens the historical version of the target note at the link's creation date using `obsidian-git` diff views.

### AI Agent Workflow
When an [[AI agent|AI agent]] reads `Note A`, it checks when the line containing `[[Note B]]` was committed via `git blame`.
If `git log --since="<link_date>" -- Note_B.md` returns commits, the agent reads `git show <commit_at_link_date>:Note_B.md` to ensure reasoning reflects the author's original context.

### Comparison to Manual Hash Links
- **Zero effort:** Keeps standard `[[note]]` syntax rather than manually hunting for commit SHAs (`[[note@sha]]`).
- **Markdown purity:** Avoids polluting notes with ephemeral hashes.
- **Active drift awareness:** Highlights when context has drifted over time, rather than leaving links silently outdated.

### References
- [[linking to git commits and diffs in obsidian via uri]] — Manual commit URIs (`[[note@sha]]`) that temporal integrity replaces.
- [[2026-07-31 historic obsidian links]] — Extracting historical graph edge birth/death timestamps from Git.
- [[how to keep history]] — Preserving Git timestamps required for temporal resolution when moving notes across submodules.
- [[agentic note taking]] — AI agents inspecting past revisions based on when a task was formulated.
- [[differentiate between AI and human notes]] — Distinguishing whether a historical link was created by a human or an AI agent.
- [[Obsidian plugin - Git]] — Underlying Git engine providing local logs and diff views for temporal resolution.



