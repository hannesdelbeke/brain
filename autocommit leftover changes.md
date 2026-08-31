---
date: 2026-08-28
created: 2026-08-28
tags:
  - technical
  - git
  - agents
  - pkm
  - workflow
aliases:
  - pickup uncommitted changes
  - uncommitted and unpushed changes
  - commit pickup
  - autocommit leftover changes
  - uncommitted & unpushed changes
---

# Autocommit Leftover Changes

The protocol for AI agents handling uncommitted or unpushed working tree edits in a [[personal knowledge management|PKM]] repository.

Related: [[public/github co-authors for AI|github co-authors for AI]], [[public/git author|git author]], [[public/git history|git history]]

---

## 1. The Core Protocol

When an [[public/AI agent|AI agent]] starts a turn and encounters uncommitted or unpushed modifications in the working tree:
1. **Presume Human Authorship:** Agents are expected to commit and push their own work before finishing their turn. Therefore, uncommitted edits found at the start of a turn are assumed to belong to the human user.
2. **Commit Under Human Identity:** Commit the staged files using the human user's git author identity (e.g. `Hannes Delbeke <3758308+hannesdelbeke@users.noreply.github.com>`).
3. **Format Commit Message:**
   - Prefix with `autocommit: <summary>` (e.g. `autocommit: update day 2026-08-28 reflections`).
   - Append the active AI model as a `Co-Authored-By:` trailer per [[public/github co-authors for AI|github co-authors for AI]] (e.g. `Co-Authored-By: Antigravity <antigravity@users.noreply.github.com>` or `Co-Authored-By: Claude <claude@users.noreply.github.com>`).
4. **Push Upstream:** Push the autocommit upstream to ensure the human baseline is recorded in remote version history before making AI-driven passes.

---

## 2. Multi-Agent Provenance & Safeguards

When multiple agents run concurrently in the same repository:
* **Sweep Only Cold Files:** A file nothing has written to for ten minutes is plausibly the human's. A file modified inside that window is plausibly a live agent's, so leave it alone and say so in the response instead of committing it. `git status --porcelain` lists the candidates and `find "<file>" -mmin +10` confirms one is cold.
* **Preserve Git Provenance:** Avoid committing agent code under human author without AI trailers, as git blame and review history depend on clear attribution. The presumption of human authorship in section 1 only holds for a cold file.

## issues
multi agents working in same vault human commit each others work

### Related
- [[proposal - agent git workflow tooling]] — this protocol as the attribution section of the wider workflow-tooling proposal