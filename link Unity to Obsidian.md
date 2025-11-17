To [[public/link]] [[Obsidian]] [[note taking|notes]] to [[Unity]]:
1. Click `Copy Obsidian URL` from the right-click menu of a note in Obsidian
2. Paste the URL in a Unity note with [[Unity note editor]].

## Dev
Obsidian has a [[URI]] scheme to open files & vaults.
   `obsidian://open?file=public/link Obsidian to Unity`
We can use this in Unity.

> [!idea]-
> don't think we need this anymore.
> - a plugin that adds support for wikilinks in Unity notes
> 	1. link to an Obsidian vault
> 	2. click `[[my note]]` to open `my note` in Obsidian
> 	- how would the user edit the URL? no WYSIWYG in Unity editor tools
> 		- could have an edit/view tab in the inspector, or an edit & save button