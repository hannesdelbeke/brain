---
tags:
  - technical
  - git
  - obsidian
  - pkm
origin-sha: e292143a2af13162fcbababd58789a7138cfc2d5
created: 2026-08-20
---
Moving notes across [[git submodule|Git submodule]] boundaries severs [[git history|commit history]].

### Submodules Don't Share History
A Git submodule is an independent `.git` repository. When a note moves across submodule boundaries (such as from root `pkm` to `public/`), standard file operations record a deletion in the source repo and a fresh file creation in the destination repo.

This severs `git log` and `git blame`, breaking [[provenance]] for:
- **Dates**: see [[moving files across submodules loses created date]]
- **Authorship**: see [[human vs ai text context]]

### Full History Transfer
For non-sensitive notes where the full commit trail is safe to share publicly, you can migrate the exact commit history directly:

```bash
# 1. Export all commits touching the note from source repo
git log --pretty=email --patch-with-stat --reverse -- "note.md" > /tmp/note_history.patch

# 2. Apply the patch sequence into the destination submodule
git -C "public" am < /tmp/note_history.patch
```