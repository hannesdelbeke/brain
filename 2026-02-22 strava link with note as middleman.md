---
views: 16
last viewed: 2026-02-22
---
I wrote about autocomplete and linking to my data (e.g. Strava activities):
- [[2026-02-19 Obsidian auto complete app URI]]
 - [[Turning Obsidian into a data lake]]

1. there's a Strava sync plugin for [[obsidian]], that makes a note for each activity, and each note has a link to the activity.
2. with the plugin [[obsidian-sentinel]] I can run actions when i open a note.
   I could set up an action that runs when I open a Strava note, to open the Strava link it contains, and close the Strava note. This has the same effect as [[sync URL shortcuts to obsidian vault|linking to URL shortcuts in my vault]], but with a complex plugin setup, and a [[wrapper note|in between note]] that acts as a middle man.

Cons
- complex setup, with exceptions. ([[2026-02-22 Obsidian track note view|Obsidian track note view]])

Pros: 
- [[Obsidian autocomplete]] support out of the box
- activities are [[backup|backed up]] in the [[Obsidian vault|vault]], in case Strava ever goes down

this is kind of similar to [[embed Google Drive folder in Obsidian]]

I don't care much for my Strava [[data]], I mostly use it as an example. Since it's easy to grasp. If I can think of a good system for this, then I can likely extrapolate the approach to my other data.