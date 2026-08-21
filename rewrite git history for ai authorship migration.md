---
tags:
  - technical
  - git
  - ai
---
Technical plan for retroactively updating Git commit metadata to accurately reflect AI vs. human authorship in legacy notes.

## One-Off Git History Migration Strategy
A Python script using `git log -p` and `git-filter-repo` can be used to scan past commits and rewrite history:

1. **Identification:** Scan historical commits and identify AI-generated blocks based on [[algo to differentiate between AI and human notes|heuristics]].
2. **Commit Splitting:** Split mixed commits into a human commit (prompt and notes) followed by an AI commit (generated response).
3. **Submodule Integrity:** Preserve submodule pointers so child repositories remain untouched.
4. **Downstream Sync:** Downstream consumers (like the [[2026-08-18 pkm voice agent addon install|telegram bot]]) must perform a single `git reset --hard origin/main` after the rewrite to sync properly.

> [!warning]
> Updating historical Git commits via force push is viable as a one-off migration, but should be avoided for routine updates.

### Related
- [[algo to differentiate between AI and human notes]]
