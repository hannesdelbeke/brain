
### Documentation
We write about our game, brainstorm, documentation, ...
store it in 
- [[Google Drive]], [[Dropbox]], [[OneDrive]]  cloud storage
- [[Miro]], [[Notion]] cloud app
- [[Obsidian]] (local / git repo)
**A cloud or local app. Notion / Obsidian**

[[2025 Unity notes feedback]]

#### Documentation links
Docs should link to assets in the Editor.
*Docs for a material that only works with a certain shader, contain a link that selects the shader in the editor.*
- [[link Obsidian to Unity]]
- [ ] Todo Unreal / Godot

#### Backlinks
I can select an asset, and see which pages link to it.
Improves discovery, and makes flow smoother.
[[backlink]]

#### Notes on assets in editor
Writing small [[note taking|notes]] on assets is powerful.
In the editor, we can link to relevant documentation
- [[link Unity to Obsidian]]
In the editor, we can link to other related assets.
- [[link Unity asset to asset]]
We can write reminders for ourselves, or warnings for others, or just info.
- [[Unity asset chat idea]]
We could link to a task ticket ([[JIRA]], [[clickup]], [[Notion]], [[GitHub]])

Why limit to text? Link drawings, link sounds, ... 
Slack does this in Files tab, Miro and Notion support it, but none integrate with Unity.

**Notion**
If e.g. you use mainly Notion, it makes sense to use notion as your database. And link assets to Notion data. Then all asset notes live in Notion, 
- asset notes are searchable, 
- asset notes support user comments: [[Unity asset chat idea]]

This means we use a database, so need to ensure we keep the database and link in the project (e.g. in a certain git branch, for a unity asset) in sync.
issue:

#### Branch link integrity
if Notion links to an asset, that exists in 1 branch, and is deleted in another.
#### Historical link integrity
If Notion links to the correct asset in the past, but now we merged the asset with another asset, so we should update the link in Notion to another asset.
If we update Notion, it will be incorrect when we roll back in git for testing.
We only will have good "flow" for the current state of the project, not past states.
- [[temporal integrity]]
#### A [[monorepo]] leads to automatic link integrity
If instead the link data lived in the editor, it would be saved in git, and it still could be different between branches, but it would auto follow the right asset, and always show the right info for the asset at that state in time. (different state between branches, past vs present state)

This avoids the need for a manager to sync with an external source (Notion), since all links are managed in the repo.
However, in reality we still need to sync between apps. E.g. Obsidian and Notion.
To avoid this, we can save our Obsidian vault in the same repo as our project: a 

In reality, external systems are often temporal, e.g. a task planner only is needed for the present and future, we don't care as much about maintaining historic links. Once a task is done, it might as well be deleted. We likely only care about it from a analytics POV, which likely doesn't require an active link.

Currently, I can't think of other external systems. Except maybe tools and workflows. It'd be great to support workflows linked to a state.
If the workflow is linked to an asset, the user should be able to easily use
- the old workflow for the old assets
- the new workflow for the new assets

When we roll back, it auto rolls back the workflow links, pointing to the old workflow docs and tools. Opening the old tool, etc.
A monorepo with links in the project would already achieve this. Since Unity tools are saved in the repo too.

## Tools & workflows
- we store tools in a repo / server
- we [[file distribution|distribute]] tools to artists 
	- [[distributing tools - tool installer]]
	- [[tool distribution]]
	- [[plugget]]
- users can easily discover tools, and easily run them
	- [[tool launcher]]
	- [[Unity tool launcher]]
	- Good [[documentation]]
	- [[unimenu]]
	- [[buttonizer]]
- users want to modify their environment.
	- run their own tools
	- create their own shortcuts
	- tweak their own [[Maya shelf]] (Avoid shelves, they are tricky)
	- [[favorite]] / [[favorite tool]]

### Link tools & workflows
add interactive tools to assets. 
- Sometimes a wizard, that talks you through the export pipeline / process.
- Or a validator tool
This could be achieved if we have links to scripts or tools in the editor
- it could be saved in the note
- it could live in some meta data
