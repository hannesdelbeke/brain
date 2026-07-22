follow up [[2026-02-22 Obsidian track note view]]

the automation that updates [[view count|viewcount]] each note is working but also causes issues.
- now that each note auto adds a [[YAML front matter|frontmatter]] on creation to store viewcount in, I have to press arrow down before I paste text, to ensure the cursor is at the bottom of the frontmatter, to prevent breaking the frontmatter.
- the auto update each view
	- breaks my recently edited files view, which now shows recently viewed.
	- always changes a file when viewing, so triggers a git edit. 
		- This creates git history clutter.
		- This broke git sync a few times 
			- [[obsidian git backup can fail]]
			- [[2026-07-13 vault backup issue]]
		  causing potential backup issues. It seems the [[Obsidian plugin - Git]] can't handle too many edits in one go before getting stuck, requiring a manual git sync to get unstuck.

- [ ] what could be a better approach?

Core issue: mixing analytics with content
analytics polute source content
Instead of writing to the note, store viewcounts in a single file:
.obsidian/viewcounts.json
Challenge, what if a note renames.
create a hook that runs on file rename
### alternatives
i researched alternatives and forks here: [[obsidian viewcount rnd]]

https://github.com/tahayigitmelek/note-radar
does this too, but 0 stars
data saved in a json in the plugin folder.

https://github.com/decaf-dev/obsidian-view-count seems to do this
⚠️ development is dropped.
i dont know how the tech works under the hood
reddit [post](https://www.reddit.com/r/ObsidianMD/comments/120fcuq/plugin_request_note_view_trackercounter/)
fork https://github.com/Moyf/obsidian-view-count

forked it
added feature to import custom frontmatter fields `views`
imported my old view data successfully, seeing it in obsidian viewcount
removed rule from [[obsidian-sentinel]] and disabled plugin. 
	which i setup originally here [[2026-02-22 Obsidian track note view]]

