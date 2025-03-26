create [[note taking|notes]] in [[Unity]], e.g. for [[documentation]]

might be useful to link [[Obsidian]] to unity.
create some kind of living documentation during gamedev

Assets and gameobjects have different approaches of attaching notes.
- some assets (e.g. prefabs) can have components, just like gameobjects.
- most assets can't have components, so we need a different approach.

- [[Unity inspector notes for folders & assets]]
	- notes on assets
	- support urls & links to assets
	- richtext
- [[Unity - add notes to gameobjects]]
- [[Unity asset chat]]

## alternatives 
- https://github.com/plyoung/**EdNotes**
	- Add notes to gameobjects in scene.
		- GameObject notes are kept in a hidden object tagged as `EditorOnly`
	- add notes to assets
		- Asset Notes are kept in an asset next to the this tool's scripts.
	- Matches Unity's UI
	- supports color tags & icons
	- a recent [fork](https://github.com/mhardy/EdNotes) adds inspector support
- https://github.com/rstecca/UNotes ugly colors
- https://github.com/sverdegd/NotepadToolUnity not notes for assets or gameobj, instead this is just sticky note assets?
- https://github.com/wataru-ito/AssetMessenger custom popup, feels clunky, add notes to assets.

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