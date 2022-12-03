
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

### same concept
- [[Google Keep]] lets you link private notes on shared docs in the google Workspace
- annotate external files (pdf) & save comments in an .md file with the [annotator](https://github.com/elias-sundqvist/obsidian-annotator) Obsidian plugin. It has nice example GIFs.
- [[Hypothesis review]] lets you annotate any website (private or public)

### Notes
- Similar to [[Obsidian private comments]]
- Similar to [[Obsidian submodule]], because we don't want to share submodules with everyone.
- similar to [[save quotes n lines]], we reference external data that can't reference back. (Sometimes even physical media like books)
- Relates to [[add notes to explorer]]
- The need for private comments is described in this google slides [discussion](https://support.google.com/edu/classroom/thread/13728889), There's no real solution but a workaround is to use copies of the slides.

- Except for a plugin in every single app, to link to Obsidian. Are there other solutions? 🤔
  Maybe we can embed every app into another app, that keeps track of notes?

> [!TODO] fleeting notes
> look at [fleeting notes](https://www.fleetingnotes.app/), it has both a [chrome extension](https://chrome.google.com/webstore/detail/fleeting-notes/gcplhmogdjioeaenmehmapbdonklmdnc) & Obsidian plugin.
> sync notes from the web ([[Chrome]]) to obsidian, and maintain a link

### challenges
If linking to a specific line, what happens if the line changes?
let's link to the whole doc, or thread for now.

[[link]]