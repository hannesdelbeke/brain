---
tags:
  - obsidian
  - technical
  - pkm
---
[[Obsidian]] supports [[wikilink|wikilinks]] inside [[YAML front matter|frontmatter]] properties (since Obsidian 1.4+), provided they are wrapped in quotes.

## Syntax & Formatting
Because unquoted brackets (`[[...]]`) break standard YAML parsers, wikilinks in frontmatter must always be enclosed in single or double quotes:

```yaml
---
related: "[[Note A]]"
references:
  - "[[Note B]]"
  - "[[Note C]]"
---
```

When using Obsidian's visual **Properties** editor (set to Text or List type), Obsidian automatically handles quoting under the hood.

## Native Obsidian Behavior
- **Graph View & Backlinks:** Quoted frontmatter wikilinks are fully indexed, connecting nodes in the graph view and appearing in the backlinks pane.
- **Auto-rename:** Renaming a target file automatically updates the quoted link inside the frontmatter.
- **Dataview queries:** Dataview interprets quoted links as link objects, allowing queries like `WHERE contains(related, [[Note A]])`.

## External Tool Compatibility
While Obsidian parses quoted frontmatter wikilinks natively, external tools (static site generators, standard markdown parsers, Linter plugins) treat them as plain strings unless specifically coded to resolve wikilink syntax.
