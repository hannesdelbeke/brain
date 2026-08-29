---
aliases:
- viewcount
- note view count
- track note views
created: 2026-02-22
energy: 5
tags:
- technical
- pkm
- obsidian
---

## Why track note views

Tracking view counts helps identify high-traffic crossroads and hub notes across an [[Obsidian vault]]. Frequently viewed notes serve as navigation waypoints and active topic hubs.

However, view counts only measure human navigation frequency, not necessarily deep conceptual value. A lightweight index note might have high views simply because you route through it, while a dense technical synthesis note might have few views but high utility. For agent-driven systems, see [[2026-08-27 every read is a write - co-retrieval as synapse strength]].

## Architecture: never mix analytics with note content

Early setups stored view counts directly in [[YAML front matter]] on each file open. This caused critical issues:
- Polluted note edit timestamps, breaking recently edited file lists.
- Flooded [[git history]] with automated commits for passive reading.
- Triggered constant file change events that stalled automated backups. See [[2026-07-13 vault backup issue]] and [[obsidian git backup can fail]].

**Core rule:** Store telemetry and access metadata in standalone plugin files (e.g. `.obsidian/view-count.json`), never in the note markdown files themselves.

## Implemented setup

- Using `obsidian-view-count` ([Moyf/obsidian-view-count](https://github.com/Moyf/obsidian-view-count) fork) with frontmatter sync disabled.
- Listens to workspace note open events and records timestamps to plugin storage.
- Listens to vault rename events so view statistics follow renamed notes automatically without file corruption.

## Related notes
- [[2026-07-22 follow up Obsidian viewcount]] — fixing Git backup stalls and migrating off frontmatter
- [[2026-02-22 Obsidian track note view]] — archive of original frontmatter-based view tracking setup
- [[Obsidian data worth exposing to AI agents]] — exposing view frequency and recency to agents
- [[2026-07-13 vault backup issue]] — investigation into backup failures caused by view telemetry
