Can we solve the problem where a [[Obsidian callouts|callout]] on first line in obsidian doesn't render if we open note, and cursor is on first line?

### Cause
In Obsidian Live Preview (CodeMirror 6), markdown syntax unmasks on the active cursor line. Opening a note places the cursor at line 1 position 0 by default, forcing line 1 `> [!NOTE]` into raw edit mode instead of rendering the widget box until you click away.

### Solutions
- **Blank line / frontmatter buffer:** Start note with `---` frontmatter or a blank line on line 1 so the cursor lands above the callout.
- **Reading view (`Ctrl + E`):** Disables active-line unmasking completely.
- **[[Obsidian plugin - Remember cursor position|Remember cursor position plugin]]:** Restores cursor to last position (or end of note) instead of defaulting to line 1.
- Deselect cursor from any lines when opening a note.

relates
- [[Obsidian improve callout formatting]]
- [[Obsidian plugin - Remember cursor position]]
