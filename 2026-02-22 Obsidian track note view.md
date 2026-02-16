---
views: 28
last viewed: 2026-02-23
---
Yesterday, when writing [[Obsidian - one way wikilinks]] - a potential solution to  how [[Obsidian backlinks]] become [[visual clutter|visually cluttered]] when it's linked too often - I was reminded of [[Link strength]]. Today I wanted to see if I could calculate this based on note [[view count]]. 

Ideally we also track time spent on the note, but that seems more complex to track. 
[[view count]] might be high for notes with little value, e.g. the [[link]] note has not much in it. But it's an important concept, often mentioned in other notes. 

And we might just often navigate through a note, increasing it's viewcount. However, notes we often navigate through also have value, they are like crossroads, or important hubs in our knowledge graph, without them we wouldn't find the notes that mattered. So tracking views is a good start.

## View count
To track views in my [[Obsidian vault]]

1. Install the plugin [[obsidian-sentinel]]

2. Add new action
	**Where** left empty
	**if** `Opening a note once, reset on closing the note`
	**property** `views` 
	**value** `{{increment}}` 

	This will increment each time the note is opened, and reset to 0 when the note is closed.

3. setup [[obsidian-dataview]] to show notes sorted by views.

----
## Last viewed date

if you want to track the date of last viewed: Add an action
	**Where** left empty
	**if** `Opening a note once, reset on closing the note`
	**property** `views` 
	**value** `{{date:DD-MM-YYYY-MM}}` 

This can be usefull since [[most recent]] notes might be the most relevant

---

I already use [[supercharged links]] for [[Obsidian - color links based on folder]]
But I could use it to color notes with many views, or recentlly viewed notes.
