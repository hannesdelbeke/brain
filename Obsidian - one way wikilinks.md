---
views: 4
---
Standard [[wikilink|wikilinks]] are of the format `[[note title]]`.
In Obsidian, they show up in the [[Obsidian backlinks]] panel.

But sometimes, we might want to have a one directional link, instead of a bi-directional link.

## Problem
Popular notes, like [[Obsidian]] or [[Windows]], are linked from many notes, but they don't need to link back to those notes. The [[Obsidian backlinks]] panel looses its value, once the user becomes overwhelmed. For me, it get's the most value around up to 20 backlinks.

## Idea
What if we could type a one directional wikilink `[[>note title]]`? 
Like this: [[>note title]].

Add support for a link that is navigational, not relational.
“I want to reference a note… but I don’t want to create a relationship.”

Another approach to make links more relevant is to 
- define the [[link type]], instead of dumping everything in backlinks. And split it by category, e.g. example, backlink, reference, ...
- set a [[Link strength]], so you can say this strongly relates, or this weakly relates. And sort by link strength, so the most relevant results show at the top.
## Plan
It seems [[Obsidian]] doesn't support this (at least on [[Windows]]), since a file name can't contain `>`

We could create a custom Obsidian plugin that supports this:
- we need a handler that, if a link starts with `>`, opens that [[note taking|note]].
- we need to handle css, to pass on the state of the note (exists or not existing)
- subscribe to the rename note event
- likely other things to handle or note events to subscribe to

then we have one directional [[wikilink]] support.
- The [[Obsidian backlinks]] panel won't include these links
- clicking the wiki link opens the note

Extra:
- [[MkDocs materials]] might need extra support for this.
- other workflows from other users might need similar updates.

## Conclusion
Lots of technical work, with a lot of edge cases to handle, for a small UX improvement.

---
## Existing one directional links

#### Obsidian URI
[[Obsidian URI]] can [[URL]] link to a note in a vault, but it's not as user-friendly as [[tabbing]] in a wiki link with [[Obsidian autocomplete]].
e.g. `obsidian://open?vault=...&file=Some%20Note`

#### Markdown links
`[Obsidian](<Obsidian.md>)`
cons
- [[markdown link dont support spaces]]
- no [[autocomplete]] without a plugin like _Link Favicons_ or _Markdown Links_

#### Frontmatter
Use [[YAML front matter|frontmatter]] fields as one‑directional links

---

[[Obsidian plugin ideas]]