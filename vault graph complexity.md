let's track issues that we need to keep in mind in this note
no solutions in this note, tracking only

issues
- **Meta-tagging confusion:** Using the `#archive` tag just to talk about it (e.g. "see #archive for all notes") accidentally marks the current note as archived in queries.
- **Submodule Link Leaks:** Notes in a public/work submodule accidentally linking to private root notes. When the submodule is cloned elsewhere, these links break or leak private file names.
- **Dead Synapses (Broken Links):** Hard-deleting obsolete notes (pruning) creates broken/orphan wikilinks across the rest of the vault graph.
- **Temporal Disconnects:** Moving notes between folders or submodules breaks their original file creation dates and Git history, forcing us to inject `origin-sha` pointers to maintain the chronological graph.
- **Duplicate YAML Keys:** Scripts that accidentally inject duplicate frontmatter keys (e.g., two `origin-sha` fields) silently break YAML parsers across the vault, destroying metadata indexes.
- **Hashtag Fragmentation:** Using hashtags instead of wikilinks for concepts fragments the graph because hashtags don't support aliases (e.g., `#ai` vs `#artificial-intelligence`), meaning related ideas don't cluster.

[[Obsidian vault]]
