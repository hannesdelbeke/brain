What if [[wikilinks]] to other websites just worked?
Currently it's only local vault files.

### prototype
during wikilinks batch script [[note-link-janitor]] 
we register a list of websites, then we can use wikilinks logic.
- detect if www.hannes.com is in the URL, if it is, look for last bit in URL `/name of file`
- and reverse: if you get a wiki link, and it doesn't live in your vault. 
  register hannes.com in a list, and then obsidian will download a index list from hannes.com, and detect `[[name of file]]` in there.
  Note: clashes are unavoidable, in that case prioritize top result in your list.
  Good habit could be name of site encoded in your wikilinks title. or some unique ID zettelkast style.

#toolidea 