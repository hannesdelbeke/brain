# Obsidian to unity
- option to use links in [[Obsidian]], that browse to a file in [[Unity]]

Unity supports [[app URI]] via `unityhub://` but does not have built-in direct file-opening support. 
```markdown
[Open My Unity Project](unityhub://open?path=C:/Path/To/Your/UnityProject)
```
[[Unity deeplink RnD]]

# Unity to Unity
 - [x] unity notes, that link to other Unity assets. https://github.com/hannesdelbeke/unity-note-editor
	- [x] GUID links to other assets
	- [ ] wikilinks to other assets (BONUS)
- [x] some kind of note parser, with plugin support, to convert these links to clickable links in rich text.

- [[Unity notes]]
- [[Unity inspector notes for folders & assets]]
- [[Unity - add notes to gameobjects]]
e.g.
```
this prefab is used in the following scene: 
[Scene1.unity](unity://open?scene=Assets/Scenes/Scene1.unity)
```
- it'd be great to support right-click on an asset to generate & copy the link.

think this will tie into [[Unity - local UPM package installer]]
[[Unity local manifest issue]]


---

# Unity to obsidian
- [x] http or URI scheme to open a file in Obsidian.
   `obsidian://open?file=public/link Obsidian to Unity`
   Copy the Obsidian URL from the right-click menu of a note in Obsidian

don't think we need this anymore.
- a plugin that adds support for wikilinks in Unity notes
	1. link to an Obsidian vault
	2. click `[[my note]]` to open `my note` in Obsidian
	- how would the user edit the URL? no WYSIWYG in Unity editor tools
		- could have an edit/view tab in the inspector, or an edit & save button
# Unity rich text
- help menu in tool can link to rich text reference [docs](https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/StyledText.html)
- [[Unity inspector notes for folders & assets]]
- [[Unity - add notes to gameobjects]]
