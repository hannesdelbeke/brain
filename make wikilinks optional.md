---
energy: 5
sentiment:
- 6
sentiment-hash: 0a663ae4
sentiment-label:
- analytical
tags:
- technical
- planning
- communication
- work
- hobby
---

make wikilinks optional for human users

in [[Obsidian backlinks]] i can see all notes linking to a note.
this requires a [[wikilink]] in that note.
it also shows `unlinked mentiones`.

it would be nice if a wikilink was auto created on all words in all notes.
but instead of typing `[[]]` around the word to make the link.
the view auto adds a link if the wikilink exists.
so no source data is changed, no [[git history]] clutter.
user can still override and add manual links.
but if there is no link, we can rely on auto link.

### pros
- it would prevent the need to often select a word and type `[[`
- more links, more context.
- `[[ ]]` create clutter in a raw note. however it does help explicitly show what is linked and what is not.
### cons
- this might break things like [[static site generator]] for [[public notes]]
  if no support for this is added to the generator.
- could link to the wrong thing. e.g. if I have multiple notes for `Ben`

### Alternatives
while writing a note
plugin detects a unlinked word is available in the link database, and prompts user to add a link.

This is more explicit. so more likely to link to the correct notes.

---

This ties into with how [[AI agent]] interacts with wikilinks:
unlinked mentions aren't accessible through the [[obsidian CLI]].
so [[AI agent]] might lose context here, that a human has.
	[[Obsidian CLI + Agent Context at Scale]]
	
It would be great for agents to have access to unlinked mentions.
However i might talk about someone named Jack. and have a note about Jack, my best friend. But if they are 2 different people in that case, the AI might incorrectly assume I am talking about my friend Jack.
An [[agent skill|AI skill]] could instead say, *this unlinked mention is potentially relevant*
<<<<<<< HEAD
=======

See [[proposal - typed directional links for obsidian]] for the unified proposal.
>>>>>>> 043a9802989d5522611c6a13f19ede56b31041d1
