---
origin-sha: 7daed917eb1b008fcfe2cde2f74f88d306abddc2
created: 2026-04-29
sentiment:
  - 5
sentiment-hash: c169cf7b
sentiment-label:
  - factual
tags:
  - technical
  - git
  - pkm
---
Moving a file from a private repository to a public submodule creates a fresh initial commit, resetting the file's Git creation history.

While Windows filesystem creation metadata might temporarily survive on the local machine, it is fragile and lost across devices, cloud sync, or fresh git clones. Embedding an ISO date (`created: YYYY-MM-DD`) in [[YAML frontmatter|frontmatter]] provides a permanent source of truth that travels with the file.

## Why Creation Dates Matter for AI

**AI Contextual Weighting & Decay**
When querying an LLM or RAG pipeline over thousands of notes, creation dates act as a temporal filter. Agents can prioritize recent findings (e.g. software library APIs from the last 12 months) and apply relevance decay to older notes unless explicitly tagged as evergreen.

**Knowledge Velocity & Timeline Heatmaps**
Plugins like Dataview and visualization scripts use creation dates to generate productivity heatmaps, tracking which research areas or projects dominated specific years.

**Detecting Stale Knowledge**
Automated garden scripts can query notes created years ago that haven't been edited recently, flagging legacy tools or outdated architectural patterns for refactoring.

**Avoiding Filesystem Lies**
OS-level timestamps (`Date Created`) change whenever a folder is archived, unzipped, or cloned to a new machine. Frontmatter remains the only tamper-proof metadata attached directly to note content.

## Implementation Workflow

- **Standardize on ISO 8601:** Use `YYYY-MM-DD` in frontmatter for deterministic sorting by any CLI tool, Dataview query, or Python script.
- **Automated recovery via Git log:** Pull the true birth date from Git using:
  ```bash
  git log --diff-filter=A --follow --format=%aI -- "path/to/note.md"
  ```
  and inject it into the frontmatter `created:` field before or during cross-submodule migrations.

### Related
- [[maintain git history between submodules]] — Technical trade-offs between patch preservation and origin SHA pointers.
- [[wikilink temporal integrity]] — How link resolution depends on preserved creation timestamps.
