Just like [[TODO include project READMEs in Obsidian]], but with project wikis instead of READMEs.

e.g. bqt and plugget have wikis. 
These wiki pages are [[Markdown]] files that can be read by [[Obsidian]].
It'd be cool if I could clone and view these notes in Obsidian, so I have 1 central place to manage my knowledge.

CON
- [[wikilink|Wikilinks]] in my current notes would break, since some wiki pages share the same name as these notes. 
  E.g. I have a `Maya` note, but there's also a `Maya` note in the plugget wiki. Adding the plugget wiki in my Obsidian vault would break the `Maya` wiki link, replacing it with `public/Maya` or `plugget-wiki/Maya`
	- this in turn would break all links in the wiki, since the wiki doesn't ha the folder context of `plugget-wiki`

It's only possible if I avoid name clashes.
This might be doable with a script, that mirrors the files from an external repo, syncing and renaming them.

This reminds me of [[annotate websites]]


[[use more links in life]]