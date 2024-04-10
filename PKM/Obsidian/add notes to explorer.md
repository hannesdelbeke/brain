# Add notes to explorer
I find myself in need to attach notes to files.
e.g. this file contains this, or is used by this.

there are 3 types of notes
- local in file
- local external
- private external
when working in teams it's easier to use private notes, 
since otherwise the file will be seen as modified everytime you update a note.
Since files are binary, this won't work nice with sourcecontrol

### Local notes
local notes live in the folder or file.
	internal: notes live in the file
	external: notes live in the folder
When sharing the files with your team, the notes are usually also shared.
When moving the file or folder, the notes move with it.
external notes can be put in `.gitignore`

### private notes
private notes live somewhere else, e.g. in another folder, or a database.
They are private and don't change the file.
The external manager needs to handle folder moving, else note pointers will break.

## Solutions

### Text file LOCAL
Save a text file in the folder and use windows preview to quickly read it in explorer

> [!NOTE]
> - simple &  stable
> - can't easily link to Obsidian, without symlink every file or a plugin that tracks files outside the vault, you can't expect to vault your whole hard drive.


### FileMeta LOCAL
[FileMeta](https://github.com/Dijji/FileMeta) lets you add metadata to every file.
this metadata will be saved in the file itself, and has some limitations. 
e.g. it might be overwritten by some apps.
- [ ] test how this works when committed, with filetypes I use often

> [!NOTE]
> The notes are:
> - shared with the file
> - not easily accessed in other software
> - prone to be lost or overlooked
> - can't sync w Obsidian

![[add notes to explorer-1673900509482.jpeg]]
would require some kind of plugin to be more accessible

### NoteZilla PRIVATE
[NoteZilla](https://www.conceptworld.com/Notezilla/Sticky-Notes-For-Windows) (paid 30$) nicely handles this by letting you stick notes to windows.
The UX is not perfect but ok. Seems to work well on win 11 (2023)
When pinning a note to a window, it disappears when the window is not active.
**Where does the data live?**
in a local database `%appdata%\Conceptworld\Notezilla\Notes9.db`
which uses `SQLite format 3`
(related,  [article](https://www.makeuseof.com/obsidian-dataview-notes-guide/) to turn Obsidian vault into a database)

NoteZilla covers the need to pin notes to a window, but it doesn't support bi-directional syncing with Obsidian. An Obsidian plugin could take care of this.
recreating all stickies as md files, and syncing them back to the database when they are changed.
#pluginidea

> [!NOTE]
> - notes are private, and not shared with the team
> - can't sync w Obsidian

NoteZilla links notes to folders, just like [[Google Keep]] links notes to google docs.

## other
you can't add metafile comments to a folder.
but you can 
- add them to the `.ini` file in the folder. and the comments will show on hover over the folder
- create a shortcut to the folder and add metadata to the shortcut

## Inspiration
- https://github.com/elias-sundqvist/obsidian-annotator 
	- external link to pdfs
	- local notes in .md format
	- works in [[Obsidian]] 
	[![](https://user-images.githubusercontent.com/9102856/131702952-1aa76baa-a279-474c-978d-cec95a683485.gif)]

[[WindowTop]]