
> what if we can have [[Obsidian note|notes]] for a [[tag]], and you can show this note when user clicks tag. allowing user to grow a tag into a note.

✅already possible
⌛not yet tested

Growing Frontmatter Tags into Notes
- **How it works with Frontmatter:** Obsidian parses `tags: [research]` in frontmatter and registers them into the global tag pane identically to inline `#research`.
- **Tag Wrangler & Tag Folder:** Right-clicking a tag in the Obsidian tag tree allows you to rename it globally (including inside YAML frontmatter) or create a note with the exact name `research.md`.
- **Automatic Navigation:** Plugins like *Tag Wrangler* let you `Alt + Click` any tag (in the pane or in YAML) to open its corresponding `research.md` topic note.
- **The Wikilink Replacement:** If you use `type: "[[research]]"` or `topics: ["[[AI]]"]` in frontmatter instead of `tags:`, Obsidian natively tracks graph backlinks without needing tag plugins at all.