---
tags:
  - technical
  - git
  - ai
---
Technical plan for retroactively updating Git commit metadata to accurately reflect AI vs. human authorship in legacy notes.

## One-Off Git History Migration Strategy
A Python script using `git log -p` and `git-filter-repo` can be used to scan past commits and rewrite history:

1. **Identification:** Scan historical commits and identify AI-generated blocks based on authorship heuristics.
2. **Commit Splitting:** Split mixed commits into a human commit (prompt and notes) followed by an AI commit (generated response).
3. **Submodule Integrity:** Preserve submodule pointers so child repositories remain untouched.
4. **Downstream Sync:** Downstream consumers (like mobile voice agents or Telegram bots) must perform a single `git reset --hard origin/main` after the rewrite to sync properly.

> [!warning]
> Updating historical Git commits via force push is viable as a one-off migration, but should be avoided for routine updates.

### Related
- [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]]
- [[public/Obsidian Git - device author identity|Obsidian Git - device author identity]]
- [[proposal - agent git workflow tooling]] — confirms git-filter-repo is still the right tool for this, in the wider workflow-tooling proposal
