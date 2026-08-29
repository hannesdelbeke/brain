---
created: 2026-08-12
origin-sha: 01490603b2e12176b92ba68f6accd3007fb00b39
energy: 5
tags:
- technical
- planning
- obsidian
- performance
---

## Startup trace metrics (2026-08-12)

- Total startup time: 36.4s (36,437ms)
- Vault size: 10,685 files
- Open workspace tabs: 170 tabs (162 deferred)

### Main bottlenecks by duration
- Workspace layout and tabs: 13,129ms (opening default file took 10,638ms)
- `collapse-backlinks`: 12,738ms (35% of total launch time)
- `obsidian-git`: 1,402ms (scanning refs and status over 10.6k files)
- `cmdr`: 684ms
- `obsidian-icon-folder`: 440ms

## Root causes and actions

### Workspace tab hygiene
Restoring 170 tab containers took ~10.6s on startup. Even when tab contents are deferred, Obsidian still parses the layout tree JSON, builds DOM nodes for split headers, restores navigation history, and queries cache metadata for every open tab path.

Closing inactive tabs and keeping open tabs between 10–20 eliminated over 10s of launch delay.

### Defer heavy non-essential plugins
`collapse-backlinks` caused a ~12.7s UI freeze on boot. Its `file-open` event listener fired across every initialized tab leaf as the workspace hydrated, running synchronous `document.querySelector(...)` queries on unrendered DOM and triggering 170 back-to-back reflows.

Moving `collapse-backlinks` and `obsidian-auto-wikilink` to a delayed startup group in [[obsidian-plugin-groups]] removes the freeze entirely.

### Git startup tuning
Scanning git status across 10.6k files on launch took 1.4s.

In `obsidian-git` settings, deferring "Vault status on startup" and ensuring `.gitignore` ignores large binary or cache directories speeds up startup without risking backup reliability. See [[Obsidian plugin - Git]].

### Plugins to keep on immediate startup (0s delay)
- `dataview`: keeps queries on landing pages rendering instantly.
- `obsidian-tasks-plugin`: prevents task blocks from briefly flashing as raw markdown.
- `obsidian-icon-folder`, `supercharged-links-obsidian`, and `recent-files-obsidian`: prevents layout shifts, wrong link colors, and UI pop-in.

## Related notes
- [[Obsidian faster startup]] — overall optimization strategies and latency benchmarks
- [[2026-07-22 Obsidian slow]] — earlier investigation into vault lag
- [[2026-08-29 Obsidian lazy loading plugins compared]] — detailed comparison of lazy loading tools
- [[obsidian-plugin-groups]] — plugin grouping and delay configuration
