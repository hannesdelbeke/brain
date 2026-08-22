---
tags:
  - obsidian
  - bug
---
When opening a note in Obsidian Live Preview (CodeMirror 6), a [[Obsidian callouts|callout]] placed on line 1 stays unrendered in raw markdown edit mode because the cursor defaults to line 1 (`pos: 0`). Markdown widgets only render when the cursor leaves that line.

### Solutions
- [[Obsidian plugin - Remember cursor position]]: restores cursor position or places it at the end, preventing automatic line 1 unmasking.
- Start note with frontmatter (`---`) or a blank top line so the cursor lands above the callout.
- Switch to reading view (`Ctrl + E`) which never unmasks active lines.
- Unfocus the editor upon opening.

For general layout and list issues within callout blocks, see [[Obsidian improve callout formatting]].
