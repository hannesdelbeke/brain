create [[note taking|notes]] in [[Unity]], e.g. for [[documentation]]

might be useful to link [[Obsidian]] to unity.
create some kind of living documentation during gamedev

explore this project 
- [[Unity inspector notes for folders]]
- [[Unity - add notes to gameobjects]]
- https://github.com/plyoung/EdNotes better integrated in UI, supports color tags.
- https://github.com/rstecca/UNotes ugly colors
- https://github.com/sverdegd/NotepadToolUnity ugly colors
- https://github.com/wataru-ito/AssetMessenger custom popup, feels clunky

## features
- [x] write notes on folders [[Unity inspector notes for folders]]
- [ ] write notes on assets  [[Unity - add notes to gameobjects]]
- [ ] support URLs
	- [ ] optional support wikilinks
- [ ] support markdown & rich text
- [ ] support embedded images
- [ ] support private / local / user notes vs project notes
	- [ ] a dict with `{GUIDs: private notes}` in a gitignored folder.
	- [ ] ideally the GUIDs would not be textdata but unity metadata so they can auto update if GUID changes somehow.
- [ ] support instanced notes, e.g. a bunch of assets have the same note.