---
energy: 5
tags:
- technical
- obsidian
- performance
- pkm
---

## How plugin loading works in Obsidian

By default, Obsidian initializes active community plugins sequentially in the order listed in `.obsidian/community-plugins.json` during the boot sequence before workspace layout hydration.

As a vault grows, eager initialization of heavy indexers, background syncers, and complex UI plugins introduces startup latency. [[lazy loading]] and [[deferred loading]] address this by changing when and how plugins initialize:
- Time-delayed loading: core workspace renders immediately, and non-essential plugins load in the background after a configured delay.
- On-demand proxy loading: plugins stay dormant at 0ms startup cost until their commands, ribbon buttons, or views are invoked.
- Workflow or profile toggling: plugins are grouped and enabled only when needed.

## Lazy loading plugins compared

### [Plugin Groups](https://github.com/Mocca101/obsidian-plugin-groups) (`obsidian-plugin-groups`)
- Author: Mocca101
- Mechanism: organizes plugins into named groups with group-level delay timers or manual toggle switches.
- Pros: batch toggling for workflows (e.g. writing vs coding), status bar switcher, simple grouping.
- Cons: requires manual group setup; less direct for a one-off delay on a single plugin.
- Note: see [[obsidian-plugin-groups]].

### [Lazy Plugin Loader](https://github.com/alangrainger/obsidian-lazy-plugins) (`lazy-plugins`)
- Author: Alan Grainger
- Mechanism: adds direct millisecond delay settings per plugin or categorized delay buckets (immediate, short, long).
- Pros: lightweight, direct per-plugin timer control without managing groups.
- Cons: timer delays only; doesn't dynamically load on command.

### [On-Demand Plugins](https://github.com/22-2/obsidian-on-demand-plugins) (`on-demand-plugins`)
- Author: 22-2 (fork of `obsidian-lazy-plugins`)
- Mechanism: proxies plugin commands and view registrations while keeping plugin bundles unloaded. When a command or view is triggered, it loads the plugin dynamically.
- Pros: 0ms startup impact for utilities used occasionally (e.g. importers, exporters, diagramming, code runners).
- Cons: unsuitable for background indexers or syncers (like Dataview or Git) that must monitor files from boot.

### [Quick Plugin Switcher](https://github.com/3C0D/obsidian-quick-plugin-switcher) (`quick-plugin-switcher`)
- Author: 3C0D
- Mechanism: fast modal switcher with color-coded groups, tags, and startup delay timers per plugin or group.
- Pros: quick search modal to toggle plugins on the fly, combines grouping with startup delay.
- Cons: UI focused heavily on switching rather than pure headless background deferral.

### [Better Plugin Manager](https://github.com/eondrcode/obsidian-manager) (`obsidian-manager`)
- Author: eondrcode
- Mechanism: plugin control center with delayed startup profiles, tagging, conflict diagnosis, and cross-vault setup transfers.
- Pros: feature-rich management, conflict troubleshooting.
- Cons: heavier interface, installed via GitHub/BRAT.

## Plugin categorization strategy

When auditing plugins for [[Obsidian faster startup]], categorize them into three buckets:

### Immediate startup (0s delay)
- Core workspace enhancers: homepage loaders, layout stabilizers, icon/theme managers where delays cause layout shifts or visual pop-in.
- Immediate indexers: Dataview or Tasks if queries live on your landing page.

### Timer delay candidates (2s – 10s delay)
- Background sync and watchers: Git sync, backup tools, or auxiliary metadata indexers that aren't needed in the first few seconds.
- Secondary UI helpers: backlink collapsers, property formatters, and clean-up tools. See [[2026-08-12 Obsidian plugin startup optimization]] for real-world trace examples.

### On-demand candidates (command triggered)
- Single-purpose tools: importers, exporters, code runners, and format converters used only via hotkey or command palette.

## Related notes
- [[Obsidian faster startup]] — startup optimization methods and benchmarks
- [[obsidian-plugin-groups]] — dedicated note on Plugin Groups
- [[2026-08-12 Obsidian plugin startup optimization]] — performance trace breakdown of bottlenecks
- [[2026-08-29 Startup Metrics Logger devlog]] — devlog for measuring startup latency
- [[2026-08-29 Obsidian community plugin submission process]] — submitting plugins to Obsidian directory
