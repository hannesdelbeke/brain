---
tags:
  - solved
  - git
  - pkm
origin-sha: 5c842fe4b
---
When alternating commits between human and AI on [[linking to git commits and diffs in obsidian via uri]], authorship is tracked via [[git author]].

When extracting content from an existing note into a new note ([[link to git historic notes devlog]]), the new commit initially appears as a single creation event by whoever performed the extraction. However, Git can still trace the original line-by-line provenance.

### Line Provenance Across Extractions

**git blame copy detection**
Running `git blame -C -C -C` detects lines moved across files within the same commit. Testing this on the vault confirms Git traces 60+ extracted lines back to their original commits in `linking to git commits and diffs in obsidian via uri.md`, preserving the original human vs AI authorship even after text is moved.

**diff pairing**
When parsing history via `git log -p`, scripts pair simultaneous deletions in the source note with additions in the destination note to detect refactors.

*Note: This tracking only works within a single repository boundary. To preserve this data when moving notes across submodules, see [[maintain git history between submodules]].*
