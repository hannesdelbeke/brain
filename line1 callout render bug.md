---
tags:
  - obsidian
  - bug
  - solved
links: "[[Obsidian improvements]]"
---
When opening a note in [[Obsidian]] Live Preview (CodeMirror 6), a [[Obsidian callouts|callout]] placed on line 1 stays unrendered in raw markdown edit mode because the [[text cursor|cursor]] defaults to line 1 (`pos: 0`). Markdown widgets only render when the cursor leaves that line.

### Solutions
- [[Obsidian plugin - Remember cursor position]]: restores cursor position or places it at the end, preventing automatic line 1 unmasking.
- Start note with a blank top line so the cursor lands above the callout.
- Switch to reading view (`Ctrl + E`) which never unmasks active lines.
- Unfocus the editor upon opening.

These solutions also fix the [[WYSIWYG]] preview rendering breaking for [[wikilink|wikilinks]] and other [[Markdown]] formatting, when it's the first word in the note, when the cursor is at `pos 0`.

For general layout and list issues within callout blocks, see [[Obsidian improve callout formatting]].
