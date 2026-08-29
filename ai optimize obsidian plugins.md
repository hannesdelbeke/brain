---
created: 2026-08-29
energy: 5
tags:
- technical
- obsidian
- performance
- automation
---

## Used to only delay plugin startup
in past i used [[obsidian-plugin-groups]] to delay startup time for plugins.
so [[Obsidian faster startup]]
now i wonder can AI set it all up for me, and improve startup even more?

## Started using AI to set up delay setup
[[2026-08-12 Obsidian plugin startup optimization]]
AI already can setup the plugin groups for me, saving me some setup work.
i still manually approve in settings
ai then sets things up for me. and i have a simple setup. either delay on startup, or don't delay.

## Log startup plugin startup times
yet often startup can still take over 6 seconds.
and checking manually in obsidian is a PITA.
so i made a startup logger - [[2026-08-29 Startup Metrics Logger devlog]]
agent now can see what is causing delay, easier to debug.

## fix delays even more
now let's allow agent to fix delays.
i asked for ideas in [[2026-08-29 Obsidian lazy loading plugins compared]]
i thought of on demand before but never explored it more. someone made [a plugin](https://github.com/22-2/obsidian-on-demand-plugins) for it.

### View proxies (loaded on demand when file or view type opens)
- `obsidian-excalidraw-plugin` — `.excalidraw.md` drawings. See [[Obsidian plugin - Excalidraw]].
- `code-viewer` / `obsidian-code-viewer-plugin` — code file previews.
- `music-code-blocks` — ABC sheet music blocks.
- `csv-obsidian` — CSV spreadsheet views.
- `txt-as-md-obsidian` — `.txt` markdown views.
- `obsidian-map-view` — map view leaves.

### Command proxies (loaded on demand via command palette or hotkey)
- `obsidian-importer` — note import wizard.
- `global-search-and-replace` — vault-wide string replacement. See [[Obsidian plugin - Global Search and Replace]].
- `table-editor-obsidian` — advanced table formatting.
- `execute-code` — code execution blocks.
- `mermaid-tools` — diagram builder.
- `find-unlinked-files` — broken link and orphan note checker.

### Keep on delay timer or immediate load
- Delay timer (2s–10s): `strava-sync`, `view-count`, `OA-file-hider`, `collapse-backlinks`, `editing-toolbar`.
- Immediate load (0s): `obsidian-git` (see [[Obsidian plugin - Git]]), `dataview`, `homepage`, `obsidian-icon-folder`, `supercharged-links-obsidian`.
