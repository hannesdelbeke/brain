---
created: 2026-07-22
energy: 6
tags:
- journal
- technical
- obsidian
- pkm
---

## Problems with frontmatter viewcount tracking

The original view tracking setup in [[2026-02-22 Obsidian track note view]] used [[obsidian-sentinel]] to increment a `views` field in [[YAML front matter]] on every note open. While functional, it introduced severe side effects:
- Cursor paste friction: auto-inserted frontmatter forced moving the cursor past line 1 before pasting to avoid corrupting YAML.
- Broken recently edited lists: opening a note for reading updated its file modified time (`mtime`), masking genuinely modified content.
- Git history pollution and sync stalls: every note viewed generated a Git file change. During high-traffic reading sessions, rapid file changes restarted the Git timer continuously, starving auto-sync and causing backup failures. See [[2026-07-13 vault backup issue]] and [[obsidian git backup can fail]].

## Core principle: separate analytics from content

Telemetry data belongs in dedicated plugin storage (`.obsidian/plugins/.../data.json` or `.obsidian/view-count.json`), completely isolated from note content and Git commits.

## Research and tool comparison

### [obsidian-view-count](https://github.com/decaf-dev/obsidian-view-count) and [Moyf fork](https://github.com/Moyf/obsidian-view-count)
- Tracks view statistics independently in plugin storage.
- Listens to `vault.on('rename')` events: renaming or moving a note updates the internal path key in `data.json`, preserving view history without touching markdown files.
- The Moyf fork adds safety checks preventing destructive frontmatter overwrites, fixes Moment.js types, and updates the Svelte toolchain.

### [note-radar](https://github.com/tahayigitmelek/note-radar)
- Stores view stats strictly in plugin storage with a full-tab analytics dashboard.
- Missing rename event handling: renaming a note leaves an orphaned path in `data.json` and resets the renamed note's view count to 1.

## Implementation and migration

1. Forked [Moyf/obsidian-view-count](https://github.com/Moyf/obsidian-view-count) and added an importer to parse existing `views` frontmatter values into the plugin's external JSON cache.
2. Verified view history transferred cleanly into the new view count panel.
3. Removed the automated rule in [[obsidian-sentinel]] and purged legacy `views:` frontmatter lines from notes.
4. Submitted PR [Moyf/obsidian-view-count#1](https://github.com/Moyf/obsidian-view-count/pull/1).

## Related notes
- [[view count]] — canonical concept note on note view tracking
- [[2026-02-22 Obsidian track note view]] — archive of initial frontmatter setup
- [[2026-07-13 vault backup issue]] — detailed post-mortem on Git backup stalls
- [[Obsidian data worth exposing to AI agents]] — surfacing view frequency to AI agents
