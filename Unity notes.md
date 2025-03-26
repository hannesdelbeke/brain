create [[note taking|notes]] in [[Unity]], e.g. for [[documentation]]

might be useful to link [[Obsidian]] to unity.
create some kind of living documentation during gamedev

Assets and gameobjects have different approaches of attaching notes.
- some assets (e.g. prefabs) can have components, just like gameobjects.
- most assets can't have components, so we need a different approach.

explore this project 
- [[Unity inspector notes for folders & assets]]
- [[Unity - add notes to gameobjects]]
- https://github.com/plyoung/EdNotes
	- add notes to gameobjects, and assets
	- Matches Unity's UI
	- supports color tags & icons
	- a recent [fork](https://github.com/mhardy/EdNotes) adds inspector support
- https://github.com/rstecca/UNotes ugly colors
- https://github.com/sverdegd/NotepadToolUnity ugly colors
- https://github.com/wataru-ito/AssetMessenger custom popup, feels clunky

## features

MVP
- [x] write notes on folders & assets
	- [ ] V1 [[Unity inspector notes for folders & assets]]
	- [ ] V2 [[Unity note editor]]
- [x] support URLs
- [x] support rich text
- [x] support private / local / user notes vs project notes

bonus
- [ ] optional support wikilinks
- [ ] support embedded images
- [ ] support instanced notes, e.g. a bunch of assets have the same note.