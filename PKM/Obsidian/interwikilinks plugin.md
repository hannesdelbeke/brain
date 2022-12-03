What if [[wikilink]] to other websites just worked?
Currently it's only local vault files.

turns out this exists already.
it's named interwiki links, see [wikipedia entry](https://en.wikipedia.org/wiki/Help:Interwiki_linking)
doesn't work by default: [[Wikipedia:Main Page]] `[[Wikipedia:Main Page]]`

### prototype
during wikilinks batch script [[note-link-janitor]] 
we register a list of websites, then we can use wikilinks logic.
- detect if `www.sitename.com` is in the URL, if it is, look for last bit in URL `/name of file`
- and reverse: if you get a wiki link, and it doesn't live in your vault. 
  register `sitename.com` in a list, and then obsidian will download a index list from `sitename.com`, and detect `[[name of file]]` in there.
  - Note: clashes are unavoidable, in that case prioritize top result in your list. e.g. both vaults have a note named `overview`
    Good habit could be name of site encoded in your wikilinks title. or some unique ID Zettelkasten style.

# obsidian

## solution 1
changing all link behaviour in obsidian seems tricky.
LINK
- support : and change link behaviour
- change backlink behaviour
- change link expand

NAMING
- we now allow dupe names for notes. doing this in the same vault creates issues. change name behaviour
	- WORKAROUND: give all notes a unique GUID, existing plugins

## solution 2
maybe we can use `[[othervault:note]]` to launch a second obsidian and open the new vault.
- no issues with dupe name
**drawbacks** 
- still no backlinks & all other link behaviour
- need to setup plugins for every vault. (or use symlink)

[[test:test images]]
## concepts
### inter-vault backlink plugin
[ref](https://github.com/jensmtg/influx) for an alternative backlink plugin
might make sense to instead of edit the backlinks plugin, make a new one.
then we can render a section for "vault links" underneath the default backlinks

#### (local) interwiki table
each vault has an interwiki list, stating which inter-wikis/vaults it accepts and what their `sitename` is, which is used in the wikilinks `[[sitename:link]]`

#### inter-vault link
we can replace a URL in HTML/CSS with the matching [obsidian URI](https://help.obsidian.md/Advanced+topics/Using+obsidian+URI) to open a note in another vault. we need a interwiki table to resolve the links.
see [Markdown post processing]( https://marcus.se.net/obsidian-plugin-docs/editor/markdown-post-processing) to change how a Markdown document is rendered in the Reading view, can we also change live-preview?

#### global interwiki table
mediawiki.org/wiki/Extension:Interwiki see Global interwikis


#toolidea 

## A test case for Obsidian
instead of copying notes such as [[Uniform Resource Identifier|URI]], we should be able to point directly to `[[wiki:URI]]`, which then points to https://en.wikipedia.org/wiki/URI
saving me the time of looking this up on wikipedia.

## reference logseq
logseq supports interwiki links using [[app URI]], see [PR](https://github.com/logseq/logseq/pull/4881)
`logseq://graph/<graph name>?page=<page name>`
It works, but it's not as neat as `[[graph:page name]]`

could we do something similar in [[Obsidian]] ?