---
energy: 5
tags:
- devlog
- obsidian
- performance
- development
- ai-retrospective
---

# 🛠️ Startup Metrics Logger Devlog

- Created the open-source repository [obsidian-startup-metrics-logger](https://github.com/hannesdelbeke/obsidian-startup-metrics-logger) to measure and write Obsidian startup latency and per-plugin load times to structured JSON and Markdown logs for AI analysis.
- Packaged and published initial release `1.0.0` on GitHub with all required distribution assets (`manifest.json`, `main.js`, `styles.css`).
- Researched and benchmarked lazy-loading alternatives, documenting findings in [[2026-08-29 Obsidian lazy loading plugins compared]].
- Documented the official directory portal submission workflow in [[2026-08-29 Obsidian community plugin submission process]].

### 🤖 Gemini 3.7 Flash Mistakes & Retrospective
- Appended the plugin to the end of `community-plugins.json`, forgetting that Obsidian loads plugins strictly by array index and requires index 0 to time other plugins on startup.
- Implemented an `autoPrioritizeLoadOrder` routine to fix the load order issue so the plugin forces itself to index 0 on launch.
- Attempted a deprecated GitHub Pull Request against `obsidianmd/obsidian-releases` before realizing Obsidian moved submissions to `community.obsidian.md`.
- Failed to push git workflows initially by attempting to commit `.github/workflows/` with a GitHub CLI token that lacked the `workflow` OAuth scope.
- Wrote duplicate notes to the private vault root instead of creating them directly in the `public/` directory, requiring manual deletion.
- Violated Obsidian manifest naming guidelines by naming the plugin `Startup Metrics & Plugin Load Time Logger` (which contained the forbidden word `Plugin` and disallowed symbol `&`).
- Renamed the plugin to `Startup Metrics Logger` in `manifest.json` and replaced release `1.0.0` assets to fix directory validation.
