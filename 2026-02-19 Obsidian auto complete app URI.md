---
views: 4
last viewed: 2026-02-22
---
Think of an Obsidian plugin where you can 
1. subscribe to external data lists in settings (activities, memories, photos, ...)
2. these lists add entries to the [[Obsidian autocomplete]] suggestions list.
3. When you accept the suggestion (e.g. `[[Jack Arthur]]`), it adds a [[app URI]] link to the note, so you can click on the link to open the related app directly from your note. (e.g. [[Google contacts]])

it seems i could do this, if i could add to the suggested tab list in obsidian. 

> [!warning]
> below focusses more on a wrapper plugin, and less on the concept of adding to the obsidian auto complete list. but we do need the wrapper for this.

## asks
- dont rely on obsidian. the links are stored in open source app and work with other apps.
- make it generic, reusable, ...
- I want it to work with [[google contacts]], my [[Obsidian vault]], and [[Instagram]] posts, and [[Strava]], and [[GitHub]]
- how can the database be backed up?

## solution
[[sync URL shortcuts to obsidian vault]]

## brainstorm
Think of a generic wrapper.
- backup
	- e.g. local download contacts. local download memories, local download notes from Notion, ...
- subscribe (with obsidian) to URIs
	- easy create [[link|links]]: 
	  auto complete link, to open in certain apps, trigger certain actions.
- sync. 
	- e.g. between obsidian and google contacts: address, phone nr, relation (girlfriend, husband, uncle, ...)

this would solve
- [[interwikilinks plugin]]
- [[TODO link contacts to photos and memories]]

could it address [[note linking duplicate source]] ?

---

what if everything contained backlinks -> [[note linking duplicate source]]
e.g. in [[google contacts]], there's a link to the obsidian note in a text field.
Or in the memory data entry, there's a link to the obsidian note.

cons: 
harder to scale when embedded. e.g. if i link to a google photo/photo in my personal photo drive, from in my note. i don't want to go and edit [[metadata]] for that photo in the photo itself.

an external [[manager]] likely would be better.
some kind of [[database]] that tracks links. can be queried, updated on the fly, ...

## next steps
start with a wrapper for google contacts
then maybe a wrapper for google photos
then move to a generic solution

later we want to handle more complex solutions e.g. google photos is first, but if it's down we use our personal photo drive, and a resolver resolves the url from google photos to our personal drive
ignore this for now since it adds a lot of [[complexity]]
keeping everything personal and committing to one solution is easier.
google photos could be a separate service, we use on our phone only.

---

all of this is to link our [[data]] to each other.
what if we just toss it in a single folder, and rely on [[Artificial intelligence|AI]] to link it together?

[[wrapping]]

---
[[2026-02 app‑agnostic Entity Registry - copilot first pass]]