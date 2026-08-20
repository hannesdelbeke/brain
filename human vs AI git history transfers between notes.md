---
tags:
  - solved
  - git
  - pkm
origin-sha: 5c842fe4b
---
When alternating commits between human and AI on [[linking to git commits and diffs in obsidian via uri]], authorship is tracked via [[git author]].

When extracting content into a new note ([[link to git historic notes devlog]]), the new commit initially appears as a single creation event. However, Git and AI tools can still trace the original line-by-line provenance.

### Line Provenance Across Extractions

**git blame copy detection**
Running `git blame -C -C -C` detects lines moved across files within the same commit. Testing this on the vault confirms Git traces 60+ extracted lines back to their original commits in `linking to git commits and diffs in obsidian via uri.md`, preserving original human vs AI authorship.

**diff pairing**
When parsing history via `git log -p`, scripts pair simultaneous deletions in the source note with additions in the destination note to detect refactors.

**submodule boundary limit**
This tracking only works within a single repository. Moving notes across [[git submodule|git submodules]] severs Git history tracking unless commits are explicitly migrated with `git format-patch`.

### References
- [[algo to differentiate between AI and human notes]] — tracking author provenance across vault edits.
- [[wikilink temporal integrity]] — resolving historical note states by commit timestamp.
- [[human vs ai text context]] — preserving Git history when moving notes between submodules.
