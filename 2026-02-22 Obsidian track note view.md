---
created: 2026-02-22
energy: 5
tags:
- technical
- obsidian
- archive
---

#archive

> [!warning] Outdated setup
> Storing view counts in note frontmatter causes Git history churn and backup stalls. This setup was replaced with external JSON storage. See [[view count]] and [[2026-07-22 follow up Obsidian viewcount]].

## Initial concept: view counts as link strength

When exploring [[Obsidian - one way wikilinks]] to reduce [[visual clutter]] from heavy backlinks, tracking note view counts appeared as a way to quantify note centrality and traffic hubs.

Notes frequently navigated through act as crossroads in the graph. Even small hub notes gain high navigational value because other notes are discovered through them.

## Legacy setup (deprecated)

1. Installed [[obsidian-sentinel]].
2. Added an automation action on note open to increment a `views` frontmatter property (`{{increment}}`).
3. Used [[obsidian-dataview]] to query notes sorted by `views DESC`.

## Issues encountered

Writing view metadata directly into markdown frontmatter polluted [[git history]], broke recently edited sorting, and caused [[Obsidian plugin - Git]] sync failures during reading sessions. See [[2026-07-22 follow up Obsidian viewcount]] for the migration to external JSON storage.

## Related notes
- [[view count]] — canonical overview of view count tracking architecture
- [[2026-07-22 follow up Obsidian viewcount]] — migration to external JSON storage
- [[2026-08-27 every read is a write - co-retrieval as synapse strength]] — modern approach for agent-driven reading telemetry
