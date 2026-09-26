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

## Nesting Depth Costs Nothing
A quoted wikilink is indexed at **any** depth, not only in a flat property or a plain list. The frontmatter link extractor recurses into every array and every object it finds, building a dotted key as it descends, and records a link for any string that starts with `[[` and ends with `]]`. So a link under `sources.0.target`, inside a list of mappings, is indexed exactly like a top-level `related`.

Measured 2026-09-26 on Obsidian 1.9 (macOS) by writing a note with seven frontmatter shapes, letting Obsidian index it, and reading back the `frontmatterLinks` records Obsidian itself persisted to `~/Library/Application Support/obsidian/IndexedDB/app_obsidian.md_0.indexeddb.leveldb`. Five shapes produced a link, keyed by dotted path:

```yaml
---
flat: "[[Note A]]"                 # key: flat
list:
  - "[[Note B]]"                   # key: list.0
nested_map:
  target: "[[Note C]]"             # key: nested_map.target
list_of_maps:
  - target: "[[Note D]]"           # key: list_of_maps.0.target
    action: edited
deep:
  a:
    b:
      - target: "[[Note E]]"       # key: deep.a.b.0.target
---
```

The two shapes that produced nothing were the two unquoted ones, `target: [[x]]` and a flat `key: [[x]]`. YAML reads `[[x]]` as a flow sequence holding a flow sequence, so the value reaching Obsidian is a list holding a list holding the bare string `x`, which does not start with `[[` and is never recorded. Nothing warns about it and the note still looks correct in source mode, which makes a missing quote the quiet failure worth checking first.

`getBacklinksForFile` and the link resolver both walk `frontmatterLinks` alongside body links and embeds, so a deeply nested link reaches the [[Obsidian backlinks]] pane, the graph, and the auto-rename path on equal terms with a top-level one.

## The Docs Understate This
The [properties documentation](https://obsidian.md/help/properties) lists nested properties under unsupported features and recommends source mode for viewing them. That describes the **Properties editor UI**, which cannot display or edit a nested value, and not the metadata indexer, which reads it fine. Reading the docs alone gives the wrong answer about backlinks from nested frontmatter.

## External Tool Compatibility
While Obsidian parses quoted frontmatter wikilinks natively, external tools (static site generators, standard markdown parsers, Linter plugins) treat them as plain strings unless specifically coded to resolve wikilink syntax.
