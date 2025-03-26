# Obsidian to unity
- option to use links in [[Obsidian]], that browse to a file in [[Unity]]

Unity supports [[app URI]] via `unityhub://` but does not have built-in direct file-opening support. 
```markdown
[Open My Unity Project](unityhub://open?path=C:/Path/To/Your/UnityProject)
```
[[Unity deeplink RnD]]

[[link Unity asset to asset]]


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
