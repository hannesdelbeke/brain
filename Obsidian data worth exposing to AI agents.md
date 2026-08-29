---
aliases:
- exposing Obsidian metadata to AI agents
- Obsidian data worth exposing to AI agents
created: 2026-08-29
energy: 5
tags:
- technical
- obsidian
- ai
- pkm
---
## Why expose Obsidian internal state

Obsidian calculates rich metadata and runtime performance traces in memory. Because external agents run in a separate process, they can't see this state unless it's exported to disk or accessed via [[Obsidian CLI + Agent Context at Scale|Obsidian CLI IPC]].

Dumping high-signal internal caches to JSON bridges this gap without requiring slow full-vault filesystem scans.

## High-value datasets to expose

### Broken and unresolved links (`app.metadataCache.unresolvedLinks`)
Obsidian tracks every dead `[[wikilink]]` and the source notes pointing to them in memory.
- Instant dead link detection across 10k+ notes without regex parsing. See [[Obsidian find dead links]].
- Allows AI to fix typos, create missing stub notes, or add frontmatter aliases automatically.

### Active session context (active note, line, and selection)
The current focused note path, cursor position, active tab stack, and highlighted text.
- Lets you prompt an agent with context like *"explain this section"* or *"clean up this note"* without copy-pasting paths.
- Helps agents jump directly to relevant edit ranges.

### Resolved link graph matrix (`app.metadataCache.resolvedLinks`)
Obsidian's pre-computed graph topology of all incoming and outgoing connections.
- Instant graph analysis: detect orphan notes, compute note centrality, and find topic clusters at 0ms file-scanning cost.
- Suggest related links based on graph proximity.

### Search misses and zero-result queries
Logged query strings from the quick switcher or search tab that returned 0 results.
- Highlights gaps in vault terminology.
- AI can generate missing notes or add aliases and synonyms to existing notes.

### Query and runtime errors (Dataview, Tasks, Templater)
Console errors and timeouts triggered by broken inline Dataview queries, DataviewJS blocks, or Tasks syntax failures.
- AI can detect and repair broken query syntax across notes proactively before the user encounters them.

### Note interaction and recency metrics
Unique view counts, open dates, dwell time, and edit recency.
- Informs smart context retrieval by prioritizing currently relevant notes.
- Helps identify stale notes for consolidation or archiving.
- View count tracking setup and standalone JSON storage: see [[2026-02-22 Obsidian track note view]], [[2026-07-22 follow up Obsidian viewcount]], and [[obsidian viewcount rnd]].

### Startup performance traces
Per-plugin initialization milliseconds, layout ready time, and core overhead.
- AI can analyze latency logs (e.g. [[2026-08-29 Startup Metrics Logger devlog]]) to optimize delay groups and on-demand proxy loaders. See [[ai optimize obsidian plugins]].

## Related notes
- [[Obsidian CLI + Agent Context at Scale]] — official CLI IPC vs file-based retrieval
- [[2026-08-29 Startup Metrics Logger devlog]] — exporting startup latency to structured JSON
- [[2026-07-22 follow up Obsidian viewcount]] — tracking note views via standalone JSON storage
- [[2026-02-22 Obsidian track note view]] — initial note view tracking setup
- [[ai optimize obsidian plugins]] — configuring delayed and on-demand plugins via AI
- [[Obsidian find dead links]] — tracking and fixing broken links in the vault
