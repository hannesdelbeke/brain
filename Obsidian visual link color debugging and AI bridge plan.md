---
aliases:
- visual link color debugging plan
- debugging visual link separation with AI live hook
created: 2026-08-29
energy: 5
tags:
- technical
- obsidian
- planning
- pkm
---

## Visual link separation notes in vault

- [[Obsidian - color links based on folder]] — green links for public notes (`public/`), purple for private notes.
- [[Obsidian - color unlinked notes red]] — soft red for dead/unresolved links (`.is-unresolved`).
- [[supercharged links]] — plugin to decorate links with DOM attributes (`data-link-path`).
- [[conditional color obsidian header path]] — startup JS to color breadcrumbs based on public/private path.
- [[Obsidian distinguish internal & external links]] — styling external web links.

## Why green links are currently broken

1. **Empty Supercharged Links configuration**:
   In `.obsidian/plugins/supercharged-links-obsidian/data.json`, `targetAttributes` and `selectors` are empty arrays (`[]`), and `activateSnippet` is `false`. The plugin isn't injecting `data-link-path` attributes into the DOM.
2. **Empty generated snippet**:
   `.obsidian/snippets/supercharged-links-gen.css` is empty.
3. **Legacy CodeMirror 5 selectors in snippet**:
   `.obsidian/snippets/color-private.css` uses `.cm-s-obsidian span.cm-hmd-internal-link[data-href^="Public/"]`. This fails in modern Obsidian (CodeMirror 6) and doesn't match canonical short links (e.g. `[[view count]]` lacks the `Public/` prefix in `data-href`).

## AI live hook bridge for debugging

To let an agent inspect the live DOM, query computed CSS, and verify visual fixes in the active note, we can connect over an AI bridge. See [[Obsidian live hook and DOM bridge for AI agents]].

### Bridge setup options
1. **In-vault MCP Server (`obsidian-devtools-mcp` or `obsidian-mcp-connector`)**:
   - Embeds an MCP tool server directly in Obsidian.
   - Exposes `obsidian_execute_js` to run `getComputedStyle(el)`, inspect `.cm-link` / `.internal-link` elements, and query live class trees.
2. **Chrome DevTools Protocol (CDP)**:
   - Launch Obsidian with `--remote-debugging-port=9222`.
   - Agent connects directly to inspect DOM elements, CSS rules, and take UI snapshots.
3. **Local REST / WebSocket bridge**:
   - `obsidian-local-rest-api` for bi-directional event streaming and DOM evaluation.

## Action plan to fix and verify link colors

### Phase 1: Set up the live hook bridge
- Install and enable a lightweight MCP / WebSocket bridge in Obsidian (or launch with remote debugging).
- Verify the agent can evaluate JS against the active note DOM to read classes and computed colors.

### Phase 2: Fix DOM link path decorators
- Configure `supercharged-links-obsidian` (or a lean 15-line custom hook) to inject `data-link-path` or `data-link-status="public|private|dead"` on every link element across reading view and live preview.

### Phase 3: Write robust CodeMirror 6 CSS rules
- Update CSS snippet to target:
  - Public links (`data-link-path^="public/"` or `data-link-status="public"`): green accent (`#58a6ff` / `#7ee787`).
  - Private links (root notes): default theme purple/accent.
  - Dead / unresolved links (`.is-unresolved` / `data-link-status="dead"`): soft red (`#c94f4f`).
- Ensure selectors support both Live Preview (`.cm-link`, `.cm-hmd-internal-link`) and Reading View (`a.internal-link`).

### Phase 4: Live verification via AI hook
- Use the live hook to query `getComputedStyle(document.querySelector('.cm-link[data-link-path^="public/"]')).color` in the active note and verify that public links render green, private links render purple, and dead links render red.

## Related notes
<<<<<<< HEAD
=======
- [[proposal - live AI agent bridge into obsidian]] — synthesis, existing-solution findings, and recommended next step
>>>>>>> 043a9802989d5522611c6a13f19ede56b31041d1
- [[Obsidian live hook and DOM bridge for AI agents]] — live WebSocket, MCP, and DOM eval bridge architecture
- [[Obsidian data worth exposing to AI agents]] — exposing live metadata, unresolved links, and active context
- [[Obsidian - color links based on folder]] — concept and visual design rules for public vs private links
