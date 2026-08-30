let's track issues that we need to keep in mind in this note
no solutions in this note, tracking only

issues
- **Meta-tagging confusion:** Using the `#archive` tag just to talk about it (e.g. "see #archive for all archived notes") accidentally marks the current note as archived in queries.
	- [[vault synapse pruning]]
- **Submodule Link Leaks:** Notes in a public submodule accidentally linking to private root notes. When the submodule is cloned elsewhere, these links break or leak private file names.
	- see [[public/skills/private-to-public-note-promotion/SKILL|private to public note promotion]]
- **Dead Synapses (Broken Links):** Hard-deleting obsolete notes (pruning) creates broken/orphan [[wikilink|wikilinks]] across the rest of the vault graph.
	- [[public/vault synapse pruning|vault synapse pruning]]
	- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks and semantic links]]
- **Temporal Disconnects:** Moving notes between folders or submodules breaks their original file creation dates and Git history, forcing us to inject `origin-sha` pointers to maintain the chronological graph.
	- [[public/rewrite git history for ai authorship migration|rewrite git history for ai authorship migration]]
- **Duplicate YAML Keys:** Scripts that accidentally inject duplicate frontmatter keys (e.g., two `origin-sha` fields) silently break YAML parsers across the vault, destroying metadata indexes.
	- [[public/pkm metadata indexer|pkm metadata indexer]]
- **Hashtag Fragmentation:** Using hashtags instead of wikilinks for concepts fragments the graph because hashtags don't support aliases (e.g., `#ai` vs `#artificial-intelligence`), meaning related ideas don't cluster.

### Related
<<<<<<< HEAD
=======
- [[proposal - live AI agent bridge into obsidian]] — live graph/link-state access via a running-Obsidian bridge, instead of static file scans
>>>>>>> 043a9802989d5522611c6a13f19ede56b31041d1
- [[public/2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks and semantic links]]
- [[public/2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]]
- [[public/skills/private-to-public-note-promotion/SKILL|private to public note promotion]]
