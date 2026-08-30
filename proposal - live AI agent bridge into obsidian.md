---
created: 2026-08-30
tags:
- technical
- obsidian
- ai
- architecture
- proposal
aliases:
- live AI agent bridge into Obsidian
- Obsidian live bridge proposal
---

## The actual need

Six notes in this vault converge on the same unresolved problem: an external AI agent process needs a **live** channel into a **running** Obsidian instance, not just read/write access to the `.md` files on disk. Two distinct capabilities keep coming up, and they are not the same bridge:

1. **Live app/session state** — active note, cursor/selection, open tabs, search state, `metadataCache.resolvedLinks`/`unresolvedLinks`, plugin errors. Request/response is enough; no continuous stream required for most of these.
2. **Live DOM/CSS/visual state** — rendered HTML, computed styles, class names on link elements, ability to run JS in the renderer and see the result immediately. This is what [[Obsidian visual link color debugging and AI bridge plan]] actually needs and nothing file-based can give it, because the bug lives in what CSS selectors match against the live CodeMirror 6 DOM, not in the markdown.

Nothing in the six notes is confirmed working today; they're all design/plan/case-study notes.

## The concrete blocker already documented

[[conditional color obsidian header path]] has a specific, still-broken repro: a `DOMContentLoaded` listener added via the "JavaScript init" plugin, meant to color the tab-header breadcrumb green when the path contains "public", doesn't fire/work. [[Obsidian visual link color debugging and AI bridge plan]] separately diagnoses three concrete causes for the related link-coloring failure: empty `supercharged-links-obsidian` config (`targetAttributes`/`selectors` are `[]`, `activateSnippet: false`), an empty generated snippet file, and a CSS snippet still using legacy CodeMirror 5 selectors (`.cm-s-obsidian span.cm-hmd-internal-link[data-href^="Public/"]`) that can't match CM6's DOM or canonical short-form wikilinks. None of this can be verified without a way to inspect the live rendered DOM and computed CSS from outside the app — exactly capability (2) above.

## What already exists (web search, August 2026)

**For capability 1 (vault/session/metadata, request-response):**
[obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api) (coddingtonbear) has absorbed this space. As of 2026 it ships a **built-in MCP server** in the same plugin (`https://127.0.0.1:27124/mcp/`, bearer auth, self-signed HTTPS), supporting both the stateless 2026-07-28 MCP revision and older sessionful ones. It covers full CRUD + surgical section/frontmatter patching, Obsidian's fuzzy/JsonLogic search, listing and executing any command palette command, tag queries, and opening files in the UI — all against the live app, not a second copy of the vault. It does not expose `metadataCache.resolvedLinks`/`unresolvedLinks` or DOM/CSS state out of the box, but it has an **API extension interface** other plugins can register routes on, so a ~15-line companion plugin could add those. Third-party MCP wrappers around it (`MarkusPfundstein/mcp-obsidian`, `cyanheads/obsidian-mcp-server`, `jacksteamdev/obsidian-mcp-tools`, etc.) are now largely redundant now that the REST plugin talks MCP itself.

**For capability 2 (live DOM/CSS/JS-eval):**
Obsidian is Electron, so Chrome DevTools Protocol works: launch with `--remote-debugging-port=9222`, connect via `chrome://inspect` or a raw WebSocket to `webSocketDebuggerUrl`. [jjjjguevara/obsidian-devtools-mcp](https://github.com/jjjjguevara/obsidian-devtools-mcp) is purpose-built prior art for exactly this: it's an MCP server that attaches to Obsidian over CDP and exposes `execute_js` (arbitrary JS in Obsidian's renderer context, e.g. `getComputedStyle(el)`), console log capture, plugin/Svelte-store inspection, command execution, hot reload, and screenshot capture. This is a closer match to the link-color debugging plan than any REST-API-based option, because it can read computed CSS and live DOM classes directly.

**Important CDP caveat found in search:** the debugging port must be set **at launch**. You cannot attach to an already-running Obsidian instance after the fact without quitting and relaunching it with the flag — CDP has no "enable now" hook for a process already up.

**Other CDP/MCP variants surfaced:** `amafjarkasi/electron-mcp-server` and `holepunchto/electron-devtools-mcp` are generic Electron-app CDP bridges (not Obsidian-specific); `QianChenglong/obsidian-cdp-mcp` is another Obsidian-specific CDP MCP server, unreviewed here.

**Not relevant as a bridge, but relevant as a pattern:** `C:\Users\H\Documents\GitHub\obsidian-unified-search` (this vault's own plugin) already runs an in-app search modal that, for semantic queries, makes the *plugin* call *out* to an external localhost HTTP daemon (`pkm-metadata-indexer` on `127.0.0.1:44771`) and falls back to a CLI. That's the mirror image of what's wanted here (agent calling in vs. plugin calling out), but it's proof the localhost-daemon-from-inside-Obsidian pattern already works reliably in this setup, and it's a template if a custom push channel is ever needed beyond what the REST API's extension interface covers. No edits were made to that repo.

## Recommendation

Don't build a bridge from scratch for either need — both already have a maintained, purpose-fit implementation:

- **Session/metadata/command needs** ([[Obsidian data worth exposing to AI agents]], [[global search personal notes]]): install `obsidian-local-rest-api`, use its built-in MCP endpoint. If `resolvedLinks`/`unresolvedLinks` or note-recency metrics are needed beyond what it exposes, write a small companion plugin against its API extension interface rather than a separate server.
- **DOM/CSS/live-visual debugging** ([[Obsidian visual link color debugging and AI bridge plan]], [[conditional color obsidian header path]]): relaunch Obsidian with `--remote-debugging-port=9222` and use `obsidian-devtools-mcp` to run `getComputedStyle` and DOM queries against the actual broken link elements, confirming which of the three already-diagnosed causes (empty Supercharged Links config, empty snippet, CM5-only selectors) is actually rendering, before rewriting the CSS.
- Treat these as two separate, already-solved integrations rather than one unified "Obsidian bridge" project — the case for a single custom MCP/CDP server doing both hasn't been made, and would just be re-implementing what these two projects already maintain.

## Related notes
- [[Obsidian data worth exposing to AI agents]]
- [[Obsidian live hook and DOM bridge for AI agents]]
- [[Obsidian visual link color debugging and AI bridge plan]]
- [[global search personal notes]]
- [[conditional color obsidian header path]]
- [[vault graph complexity]]
