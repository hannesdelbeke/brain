> [!NOTE] conclusion
> As long as interwiki-links aren't supported for obsidian (and GitHub)
> I'll use separate vaults and normal [[wikilinks]]

problem:
- interwiki links don't work in github
- interwiki-links don't work in obsidian

A plugin could support linking to other vaults, without requiring that vault to use interwiki links for duplicate note names between 2 vaults.

Needed
- Obsidian interwiki-links (not allowed character in non existing note name)
  [[interwikilinks plugin]]
- GitHub interwiki links (currently shows as dead link)

ideally, we use normal wikilinks in the vault, then link that vault in obsidian.
so the individual vault on GitHub still uses the normal wikilinks. 
any links to external vaults won't work though on github

a interwiki link in my personal notes loads the other vault. which always prefers it's own wikilinks, and if not found then looks outside it's vault to the vault that referenced it.

#advanced #pluginidea #interwikilinks #wiki

- a [note](https://commonplace.doubleloop.net/interlinking-wikis) discussing linking digital gardens / wikis