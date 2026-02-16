often a [[single source of truth]] is seen as the perfect case.
but what if we have 2 sources of truth?

example [[backlink]]

Obsidian uses backlinks to link between files, showing you where a file was used.
Behind the scenes it creates some kind of database, scanning all files, and tracking which files are linked where.

This is a single source of truth for links in your notes, that act as source files.
- note A links to note B. 
- Note B doesn't contain a link to note A
Obsidian then builds a link database, and informs the user in the GUI that the current note, note B, is linked to in note A. However this link database likely contains 2 sources of truth. 
- when i load note A, it knows it links to note B
- when i load note B, it knows it links to note A

So what if instead of avoiding 2 sources of truth, we use a manager that auto handles the staying in sync part. Just like how Obsidian handles backlinks for us in the background?
As long as we edit files in Obsidian, and not outside it, it will work.
And if we edit files outside Obsidian, the changed file hash tells Obsidian to rebuild its linking database.

> [!example]
> 1. We link a note to a youtube video
> 2. This triggers the manager app in the background, it auto adds a link back to the note in the youtube video link database.
> 3. Now when I look at my youtube video, it informs me there are 2 related notes. I can click them to open then in Obsidian
> 
