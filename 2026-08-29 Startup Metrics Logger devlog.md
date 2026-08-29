---
energy: 5
tags:
- devlog
- obsidian
- performance
- development
---

# 🛠️ Startup Metrics Logger Devlog

- Created the open-source repository [obsidian-startup-metrics-logger](https://github.com/hannesdelbeke/obsidian-startup-metrics-logger) to measure and write Obsidian startup latency and per-plugin load times to structured JSON and Markdown logs for AI analysis.
- Implemented an auto-prioritization feature that automatically keeps the plugin at index 0 of `community-plugins.json` so it initializes before all other plugins during boot.
- Packaged and published initial release `1.0.0` on GitHub with all required distribution assets (`manifest.json`, `main.js`, `styles.css`).
- Attempted to submit the plugin via GitHub Pull Request to `obsidianmd/obsidian-releases`, but discovered PR submissions are now deprecated.
- Documented the new official portal submission workflow in [[2026-08-29 Obsidian community plugin submission process]].
- Researched and benchmarked lazy-loading alternatives, documenting findings in [[2026-08-29 Obsidian lazy loading plugins compared]].
- Encountered a directory validation rejection on `community.obsidian.md` because the initial name `Startup Metrics & Plugin Load Time Logger` violated manifest naming rules (contained the forbidden word `Plugin` and the symbol `&`).
- Renamed the plugin to `Startup Metrics Logger` in `manifest.json` and updated GitHub release assets to follow all Obsidian directory guidelines.
