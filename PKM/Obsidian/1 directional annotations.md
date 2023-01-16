### Scenario
- you want to add private comments to a slack thread for yourself
- you want to privately annotate on a shared document from your team. e.g. google-doc

### Current
the current approach is to make these notes privately, and link the source in the note. e.g. use [[Obsidian]] to manage those notes.
And have a single place for all your private comments ideally.

### Problem
There is no support for private notes in Slack (& some other apps)

There are no backlinks on the slack thread (unless I publicly post them) to my private external notes.

### Proposal
It'd be great if there was a plugin for Slack to view those private notes in Slack.
Or at least store a private link to my private note in Obsidian.

Ideally I would not have to search my notes, but could instantly see which threads have private notes attached.

Slack supports URL links to threads. We could have a database that gets the thread link, and links a note to it.
#pluginidea

> [!NOTE] Google Keep
> [google docs](https://docs.google.com/) & google sheets now supports [google keep](https://www.google.com/keep/)
> this let's you take private notes in a document. it stores a link to the doc in the note, and when viewing notes in keep from the document, it shows related notes at the top, in a related category.
> 
> Disadvantage: 
> - data lives in the cloud, only an issue when Google goes offline.
> - You need an additional sync process to get your data offline / in Obsidian. This can be quite technical. There's a Python [sync script](https://github.com/djsudduth/keep-it-markdown) on GitHub.
>   The sync script only syncs notes too Obsidian, not back to Keep. So keep notes will become outdated when updated in Obsidian.

### Notes
- The concept of annotating external files and saving the comments in an .md file is used by the [annotator](https://github.com/elias-sundqvist/obsidian-annotator) plugin, to annotate pdf's inside Obsidian. It has nice example GIFs.
- Similar to [[Obsidian private comments]]
- Similar to [[Obsidian submodule]], because we don't want to share submodules with everyone.
- similar to [[save quotes n lines]], we reference external data that can't reference back. (Sometimes even physical media like books)
- The need for private comments is described in this google slides [discussion](https://support.google.com/edu/classroom/thread/13728889), There's no real solution but a workaround is to use copies of the slides.

- Except for a plugin in every single app, to link to Obsidian. Are there other solutions? 🤔
  Maybe we can embed every app into another app, that keeps track of notes?

> [!TODO] fleeting notes
> look at [fleeting notes](https://www.fleetingnotes.app/), it has both a [chrome extension](https://chrome.google.com/webstore/detail/fleeting-notes/gcplhmogdjioeaenmehmapbdonklmdnc) & Obsidian plugin.
> sync notes from the web (chrome) to obsidian, and maintain a link

### challenges
If linking to a specific line, what happens if the line changes?
let's link to the whole doc, or thread for now.


relates to [[add notes to explorer]]

### inspiration