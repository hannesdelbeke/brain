---
date: 2026-08-19
tags:
  - technical
  - git
  - obsidian
  - pkm
origin-sha: 5c842fe4b
---
How to link to past Git revisions, commits, and diff views from within [[Obsidian note|Obsidian notes]], comparing offline, [[Uniform Resource Identifier|URI]], and snapshot approaches.

### Core Constraint
[[wikilinks|Wikilinks]] only resolve to files currently active in the [[Obsidian vault|vault]]. Linking to a historical version requires either leaving the vault (URI protocol/URL) or materializing the old version as a file.

### Materialize Snapshot
Extract an old version into the vault as its own permanent note:

```bash
git show <sha>:path/to/note.md > "History/2026-07-31 historic obsidian links (v1).md"
```

- **Pros:** Zero plugins required, works natively on mobile, searchable in Obsidian, immune to URL breakages.
- **Cons:** Minor file duplication; requires manual creation unless scripted.

### Portable Wikilink Convention
Use a structured wikilink syntax with the commit hash for tool-agnostic plain text:

```markdown
[[2026-07-31 historic obsidian links@abc1234]]
or
[[2026-07-31 historic obsidian links#^git-abc1234]]
```

- **Tool-agnostic:** Scripts and agents can regex-match `\[\[([^@\]]+)@([a-f0-9]+)\]\]` and run `git show <sha>:<path>` or trigger diffs.
- **Graceful fallback:** In Obsidian, standard link navigation still opens the active note.

### Remote Git Permalinks
Link directly to the exact commit SHA on GitHub:

```markdown
[View Historical Commit on GitHub](https://github.com/<user>/<repo>/blob/<commit-sha>/path/to/note.md)
```

- **Pros:** Zero setup, renders syntax highlighting, diffs, and blame view on web and mobile.
- **Cons:** Requires active internet and that commits are pushed to remote.

### Local Shell Command URI
The `obsidian-git` plugin does not accept commit SHAs via URI. To trigger a local Git diff for an exact commit, use the [Obsidian Shell Commands](https://github.com/Taitava/obsidian-shellcommands) plugin:

- **URI format:**
  ```markdown
  [Open Commit Diff](obsidian://shell-commands/?vault=pkm&execute=<command-id>&_sha=abc1234&_path=path/to/note.md)
  ```
- **Shell command body:**
  ```bash
  git -C "{{vault_path}}" difftool {{_sha}}^! -- "{{_path}}"
  ```

### Summary Recommendation
- **Permanent offline access:** Materialize snapshot (`git show <sha>:file > History/file.md`).
- **Scriptable reference:** Portable wikilink convention (`[[note@sha]]`).
- **Quick web sharing:** GitHub SHA permalink.
- **Automated local tool:** Obsidian Shell Commands URI.

### References
- [[wikilink temporal integrity]] — Resolves links via Git timestamps automatically without manual commit URIs.
- [[obsidian-git historical diff internals]] — Hands-on testing of URI schemes and Obsidian Git internals.
- [[human vs ai text context]] — Preserving commit SHAs when moving notes between submodules.
- [[human vs AI git history transfers between notes]] — How diffs preserve author provenance across extractions.
- [[Obsidian plugin - Git]] — Target integration for extending obsidian-git with diff URIs.
- [[agentic note taking]] — AI agents following commit URIs to learn from historical revisions.
- [[URI link to obsidian git diff - RnD]]