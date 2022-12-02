- submodule 1
	- note A
	- note B
- submodule 2
	- note A

in note B, we use [[wikilink]] to link to note A: `[[note A]]`
when we load both submodules in 1 vault, this results in a clash.
Even if Obsidian would handle this correctly, it would change the wikilink in the submodule to a relative path. `[[submodule 1/]]`
the submodule is now out of sync, we can't push files back

e.g. `Home.md` in git-wikis, prevents us from importing several wikis in 1 vault.

[[interwikilinks plugin]]
[[github wikis in obsidian & interwikilinks]]

[[git submodule]]

