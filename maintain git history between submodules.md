---
tags:
  - technical
  - git
  - obsidian
  - pkm
origin-sha: e292143a2af13162fcbababd58789a7138cfc2d5
created: 2026-08-20
---
moving notes across [[git submodule|Git submodule]] boundaries severs [[git history|commit history]], and how to balance privacy against author provenance.

### Submodules Don't Share History
A Git submodule is an independent `.git` repository. When a note moves across submodule boundaries (such as from root `pkm` to `public/` or from `work/private/` to `public/`), standard file operations record a deletion in the source repo and a fresh file creation in the destination repo.

This severs `git log` and `git blame`. In the destination repository, the note appears as if it was written in a single commit, losing:
- Historical commit timestamps needed for [[wikilink temporal integrity|temporal integrity]].
- Line-by-line [[algo to differentiate between AI and human notes|human vs AI author attribution]].
- Early drafts and evolutionary context.

### The Privacy vs Provenance Dilemma
Preserving [[git history]] across [[git submodule|submodule]] boundaries involves a strict trade-off:

- **Migrating full [[git history|Git history]]** keeps line-by-line author attribution and timestamps, but risks leaking private commit messages, early unredacted drafts, or internal notes into a public repository.
- **A single clean commit** guarantees zero privacy leaks, but loses the historical human vs AI trail in the new repo.

### Hybrid Workflows to Keep Human vs AI Context

**[[Anonymous SHA Pointer]] (Zero Public Leak — Default)**

### Rewrite git history
Rewrite [[git history]] with synthetic commits (Public Human vs AI Attribution)
If you want [[public notes]] to reflect [[human vs ai text context|human vs AI authorship]] without exposing intermediate private drafts, commit the file in two clean synthetic steps:
- Step 1: Commit the human draft with `--author="Hannes <...>"`.
- Step 2: Commit the AI edit with `--author="Antigravity <ai@antigravity>"`.

This establishes accurate author proportions in the public repository without exposing private scratch history.

### Full History Transfer
For non-sensitive notes where the full commit trail is safe to share publicly:

Patch Migration via `git format-patch`
```bash
# 1. Export all commits touching the note from source repo
git log --pretty=email --patch-with-stat --reverse -- "note.md" > /tmp/note_history.patch

# 2. Apply the patch sequence into the destination submodule
git -C "public" am < /tmp/note_history.patch
```

### References
- [[human vs AI git history transfers between notes]] — How `git blame -C` detects extractions within a repo vs across submodules.
- [[moving files across submodules loses created date]]