---
name: pkm-link-store
description: Modular LinkML + SQLite bitemporal provenance link store connecting PKM notes, agent sessions, git repos, branches, commits, files, and URLs.
tags:
  - technical
  - pkm
  - skill
---

# pkm-link-store

A modular LinkML 1.x + SQLite provenance graph store. It ingests local agent transcripts (`claude_jsonl`), git repositories (`git_adapter`), and vault notes (`vault_adapter`) into a bitemporal SQLite database with strict `(rel, src_type, dst_type)` schema validation and boundary allow/deny filtering.

## Schema
- `schema/core.yaml` — LinkML base types (`Entity`, `Edge`, `ProvenanceFields`).
- `schema/artifacts.yaml` — Domain classes (`Note`, `Session`, `Repo`, `Branch`, `Commit`, `File`, `Url`) and typed edge relations (`child_of`, `continued_in`, `derived_from`, `worked_in_branch`, `read_file`, `modified_file`, `fetched_url`, `cited_url`, `in_repo`, `on_branch`, `changed_file`, `mentions_session`, `links_to`, `wikilinks_to`, `backed_by`, `documented_in`, `made_commit`, `handed_over_to`).
- `schema/linkstore.yaml` — Top-level LinkML schema importing `core` and `artifacts`.

## CLI Usage
```bash
# Sync a Claude transcript root and a git repo into a store
python -m link_store.cli sync \
  --db ~/.pkm/stores/personal.db \
  --claude-root ~/.claude/projects \
  --repo brain=/path/to/vault \
  --allow-root /path/to/vault \
  --deny-root /path/to/private

# Sync vault notes, aliases, wikilinks, linked files, session notes, and cited URLs.
# Reads <vault>/.obsidian/pkm_index.db read-only, or scans markdown when it's absent.
# Pass nested vaults in the same call so each note gets its deepest vault's name.
python -m link_store.cli sync-vault \
  --db ~/.pkm/stores/personal.db \
  --vault brain=/path/to/vault \
  --deny-root /path/to/private

# Infer handed_over_to edges, run after `sync` so sessions have timestamps
python -m link_store.cli derive-handovers --db ~/.pkm/stores/personal.db

# Audit node/edge counts, density, and top-degree hubs
python -m link_store.cli audit --db ~/.pkm/stores/personal.db

# Query neighbors of a canonical node ID or alias
python -m link_store.cli query --db ~/.pkm/stores/personal.db --node "note:brain/foo.md"
```

## Handover Heuristic
`handed_over_to` (A -> B) is inferred when all of these hold:
- no explicit `continued_in` or `derived_from` between A and B, and they aren't from the same parent session (subagents)
- B starts 0 to 48h after A ends
- both worked in the same repo, judged from branches, modified files, and commits
- B read a note or file A modified (confidence 0.80), or both modified at least 2 of the same non-hub files or commits (0.65 for 2, +0.05 per extra, max 0.85)

A hub is a target modified by more than 10 sessions (`--hub-max-sessions`). It only affects the shared-target rule. Edges carry `source_adapter=handover_heuristic` and `evidence=shared:<canonical_id>`, and expire on the next run if they stop qualifying.

## Search Daemon Integration
`pkm-metadata-indexer/searchd.py` reads the link store read-only (`?mode=ro`) via `link_store_bridge.py`:
```bash
python skills/pkm-metadata-indexer/searchd.py \
  --vault brain=/path/to/brain \
  --link-store brain=~/.pkm/stores/personal.db
```
Then query `/search?q=...&cluster=1` or `/links?note=...` or `/health`.
