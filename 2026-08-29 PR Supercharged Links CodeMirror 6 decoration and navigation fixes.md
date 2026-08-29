---
aliases:
- Supercharged Links CodeMirror 6 fixes PR
- PR Supercharged Links navigation and decoration bugfixes
created: 2026-08-29
energy: 5
tags:
- technical
- obsidian
- devlog
- open-source
---

## Overview

Pull Request [#286 on mdelobelle/obsidian_supercharged_links](https://github.com/mdelobelle/obsidian_supercharged_links/pull/286) resolving link decoration dropouts during document navigation, unparsed syntax trees in CodeMirror 6, and missing attributes on notes without frontmatter.

## Issues resolved

### 1. `fetchTargetAttributesSync` returns empty attributes when `getFileCache` is null
- **Problem**: `new_props['path']` and `new_props['data-href']` were set *after* `if (!cache) return new_props;`. For notes without frontmatter or notes loaded before the cache initialized, `fetchTargetAttributesSync` returned `{ tags: "" }` with no `path` attribute.
- **Fix**: Initialize `new_props = { tags: "", path: dest.path }` at the top of the function so `path` is always available.

### 2. ViewPlugin drops decorations during note navigation (`app:go-back`, `app:go-forward`)
- **Problem**: In `ViewPlugin.update()`, incremental changes during full document transitions wiped existing decoration ranges without repopulating newly visible lines outside the initial synchronous slice.
- **Fix**: Rebuild decorations cleanly on `update.docChanged || update.viewportChanged`.

### 3. Asynchronous Lezer syntax tree missing on initial leaf load
- **Problem**: Calling `syntaxTree(view.state)` in CodeMirror 6 on newly mounted leaves returned `Tree.empty` before the parser worker completed, leaving link decorations unrendered until an edit event occurred.
- **Fix**: Use `ensureSyntaxTree(view.state, maxTo, 500)` with a fallback to `syntaxTree(view.state)`, and schedule an asynchronous dispatch retry if the tree is empty during initial load.

### 4. Editor leaves not refreshed on `file-open` and `active-leaf-change`
- **Problem**: Navigating between notes in the same workspace leaf did not trigger decoration recalculation on the editor instance.
- **Fix**: Listen to `app.workspace.on('file-open')` and `active-leaf-change` to dispatch editor updates across active leaves.

## PR Description Draft

```markdown
### Summary of Changes

Fixes several link decoration and navigation issues in modern Obsidian (CodeMirror 6):

1. **Always populate `path` in `fetchTargetAttributesSync`**:
   Ensures `dest.path` and `data-href` are attached even when `metadataCache.getFileCache(dest)` is null (e.g. notes without YAML frontmatter or notes loaded during initial vault hydration).

2. **Fix decoration drops during note navigation and history traversal**:
   Prevents decorations from disappearing when navigating back and forward (`app:go-back` / `app:go-forward`) by ensuring `ViewPlugin.update()` handles document switches cleanly.

3. **Ensure syntax tree availability**:
   Uses `ensureSyntaxTree(view.state, maxTo, 500)` so incremental AST parsing in CodeMirror 6 does not skip link nodes during rapid scrolling or initial leaf mount.

4. **Event listeners for note switches**:
   Subscribes to `file-open` and `active-leaf-change` to refresh editor link decorations across active leaves.
```

## Related notes
- [[supercharged links]] — plugin overview in vault
- [[Obsidian - color links based on folder]] — styling links by folder path
- [[Obsidian live hook and DOM bridge for AI agents]] — live CDP and DOM inspection architecture
