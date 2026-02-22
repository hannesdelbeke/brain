---
views: 4
---
Now that my [[Obsidian vault]] has grown big (5k notes), I start to notice that finding backlinks is becoming slower. Often when I click show backlinks it shows a loading bar, and half a minute later it starts populating a list.

1. Reverse lookup cost scales with vault size
Backlinks require scanning the entire link index.
2. Context extraction scales with file size
If your notes are long, Obsidian must parse more text.
3. Plugins amplify the cost
Especially:
• 	Dataview
• 	Supercharged Links
• 	Outliner
• 	Longform
• 	Editor syntax highlighters
These all hook into the rendering pipeline.
4. The Backlink panel is reactive
Every time you:
• 	switch notes
• 	toggle “show context”
• 	expand a backlink
• 	scroll
…it recomputes.

2026-02-22 gonna try the plugin [[obsidian plugin - backlinks cache]]

