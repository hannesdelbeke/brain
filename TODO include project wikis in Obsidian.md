Just like [[TODO include project READMEs in Obsidian]], but with project wikis instead of READMEs.

e.g. bqt and plugget have wikis. 
These wiki pages are [[Markdown]] files that can be read by [[Obsidian]].
It'd be cool if I could clone and view these notes in Obsidian, so I have 1 central place to manage my knowledge.

CON
- [[wikilink|Wikilinks]] in my current notes would break, since some wiki pages share the same name as these notes. 
  E.g. I have a `Maya` note, but there's also a `Maya` note in the plugget wiki. Adding the plugget wiki in my Obsidian vault would break the `Maya` wiki link, replacing it with `public/Maya` or `plugget-wiki/Maya`
	- this in turn would break all links in the wiki, since the wiki doesn't have the folder context of `plugget-wiki`

> [!NOTE]- Idea: mirror external file repo
> It's only possible if I avoid name clashes.
> This might be doable instead with a script
> - mirror the files from an external repo, syncing and renaming them.
> - handle file renaming, and what happens if file is renamed outside obsidian
> - handle images etc
> - exclude from git in Obsidian
> 
> ideally: if this could be contained in a git submodule, which has some kind of custom post-processing on it to change name, and change name back.
> 
> This is a lot of work, and adds [[complexity]]

### Idea: use URI
There is a way to do that: `[note in other vault](obsidian://vault/other_vault/note)` will open the note `note` in the vault `other_vault`.
[[Obsidian URI]]

1. clone separate Obsidian vault
2. open it once so Obsidian knows the vault's location
3. use `(obsidian://vault/other_vault/note)`
bonus: some kind of wiki link shortcut plugin, that replaces it with the above URI. Showing autocomplete when typing `[[]]` Enabling the user to quickly add these links.

CONS
- This breaks outside Obsidian so won't work for public notes
	- [ ] could create a script that replaces URIs with URLs to public wiki
- this doesn't work for [[TODO include project READMEs in Obsidian]], since it would create obsidian folders in my repos.
	- I could add the `.obsidian` folder to gitignore.


---

This reminds me of [[annotate websites]]


[[use more links in life]]