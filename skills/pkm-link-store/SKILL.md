---
name: pkm-link-store
description: Modular LinkML + SQLite bitemporal provenance link store connecting PKM notes, agent sessions, git repos, branches, commits, files, and URLs.
tags:
  - technical
  - pkm
  - skill
---

# pkm-link-store

A modular LinkML 1.x + SQLite provenance graph store. It ingests local agent transcripts (`claude_jsonl`) and git repositories (`git_adapter`) into a bitemporal SQLite database with strict `(rel, src_type, dst_type)` schema validation and boundary allow/deny filtering.

## Schema
- `schema/core.yaml` — LinkML base types (`Entity`, `Edge`, `ProvenanceFields`).
- `schema/artifacts.yaml` — Domain classes (`Note`, `Session`, `Repo`, `Branch`, `Commit`, `File`, `Url`) and typed edge relations (`child_of`, `continued_in`, `derived_from`, `worked_in_branch`, `read_file`, `modified_file`, `fetched_url`, `cited_url`, `in_repo`, `on_branch`, `changed_file`, `mentions_session`, `links_to`).
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

# Audit node/edge counts, density, and top-degree hubs
python -m link_store.cli audit --db ~/.pkm/stores/personal.db

# Query neighbors of a canonical node ID or alias
python -m link_store.cli query --db ~/.pkm/stores/personal.db --node "note:brain/foo.md"
```

## Search Daemon Integration
`pkm-metadata-indexer/searchd.py` reads the link store read-only (`?mode=ro`) via `link_store_bridge.py`:
```bash
python skills/pkm-metadata-indexer/searchd.py \
  --vault brain=/path/to/brain \
  --link-store brain=~/.pkm/stores/personal.db
```
Then query `/search?q=...&cluster=1` or `/links?note=...` or `/health`.
