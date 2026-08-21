---
tags:
  - git
  - obsidian
  - pkm
---
proposals on locking a wikilink in time, using [[obsidian-git historical diff internals]]

**1. Right-Click Context Menu & Command Palette (Preferred)**
- Right-click a wikilink `[[some note]]` or run `Git: Insert commit hash into wikilink` from the command palette.
- A fuzzy-search dropdown lists recent Git commits for that note (date, author, commit message, SHA).
- Selecting a commit appends the SHA anchor to the wikilink (e.g. `[[some note@abc1234]]` or `[[some note#^git-abc1234]]`).

**2. Navigation & Click Behavior**
- Standard click: Opens the live version of the note.
- Alt + Click: Opens the native `split-diff-view` / historical snapshot tab for that specific commit SHA.

*(Note: Hover previews are skipped to avoid editor clutter).*

### References
- [[linking to git commits and diffs in obsidian via uri]] — Synthesis of URI schemes, snapshots, and permalinks.
- [[wikilink temporal integrity]] — Automated background temporal resolution without manual commit hashes.
- [[2026-07-31 historic obsidian links]] — Mining Git commit diffs to discover historical link changes.
