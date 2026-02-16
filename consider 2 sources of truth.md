Often a [[single source of truth]] is seen as the perfect case.
But what if we have 2 sources of truth, and a manager?

Obsidian uses [[Obsidian backlinks]] to link between files, showing you where a file was used.
Behind the scenes it creates some kind of database, scanning all files, and tracking which files are linked where.

This is a single source of truth for links in your notes, that act as source files.
- note A links to note B. 
- Note B doesn't contain a link to note A
```mermaid
graph LR
A --link--> B
```

Obsidian then builds a link database, and informs the user in the GUI that the current note, note B, is linked to in note A. However this link database likely contains 2 sources of truth. 
- when I load note A, it knows it links to note B
- when I load note B, it knows it links to note A
```mermaid
graph LR
A --link--> B
B --(virtual link)--> A
```

So what if instead of avoiding 2 sources of truth, we use a manager that auto handles the staying in sync part. Just like how Obsidian handles backlinks for us in the background?
As long as we edit files in Obsidian, and not outside it, it will work.
And if we edit files outside Obsidian, the changed file hash tells Obsidian to rebuild its linking database.

> [!example]
> 1. We link a note to a youtube video
> 2. This triggers the manager app in the background, it auto adds a link back to the note in the youtube video link database.
> 3. Now when I look at my youtube video, it informs me there are 2 related notes. I can click them to open then in Obsidian
> 

There is always some type of dependency, and a way 2 systems can fail to stay in sync.

For [[Obsidian]], we recalculate all links according a formula.
For each [[Markdown]] file, get each [[wikilink]], and create a data entry in our link database. Then look up each file in the link database, and show backlinks.

The con is the dependency on this link database . If a user every uses the files outside of Obsidian, backlinks won't show.

We could create a JIRA link manager, and link to wiki links with JIRA IDs, like the ticket ID `[[AB12345]]`. This would look neat in our Obsidian notes, but if you ever swap to another project, e.g. by joining another company, the ticket ID might not be unique between these projects. So it only works withing your "environment".

---
> We could create a JIRA link manager ...

This is similar to how if notes are stored in your repo directly, instead of an external vault, it would be easier to link to them.
- [ ] todo link to this note

[[link|Linking]] between systems is harder than linking inside a contained system.
[[mono vs poly repo]] runs into this same issue for code dependencies.


But how many managers do we want to make?
