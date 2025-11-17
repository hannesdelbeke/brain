### Excel sheets
- Github has no excel sheet edit support AFAIK.
- I rarely edit sheets on location, always on my laptop. So a local edit mode would meet my needs.

- [x] [[Google Sheets]] has nice edit support, 
	- [x] so I will  [[keep using google drive for my sheets in my vault]]
- [x] but my drive data is not backed up.
	- I could create a startup script that auto backs up changed notes.
	- [x] Don't bother, [[Drive for desktop]] does this already
- Files on drive aren't easily linkable. For good UX when writing notes, I want a link suggestion to show when typing `[[`.
	- I could create a database of links, and a plugin to add this to obsidian suggestions. But this is a complex solution.
## port spreadsheets into my vault
- AFAIK the easiest would be to [[data migration|move the data]] from my Google sheets into my vault. Use a common [[file format]], and sacrifice some nice features from Google sheets. 
	- use a local editor for an existing [[spreadsheets]] format, like [[open office]].
	- no coding needed
	- Only a one time [[data migration]] task to go through all my sheets and move them over, converting them all to a new data format, and reviewing the formatting.
	- Consider a data format that's [[ascii]] instead of the binary [[xlsx]], since a [[git repo is not great for binaries]]
	- if sheets are stored in my [[git repository|git repo]], the data is auto backed up
## Investigate options to integrate sheets in vault
- ❌ [[tested Univer plugin]]
- ❌ [[tested sheets plusnplugin]]
- ✅ don't use an obsidian plugin, just [[Obsidian link non-supported files|link to a non-supported file format]].
I tested this, and it opens the file with the default editor, and works out-of-the-box with [[Obsidian auto complete]].
This is nice, since it's [[the best solution is generic|a generic solution]] that also works for other file types.

So I can just use [[xlsx]] (or another format) and edit it locally.
Let's [[use the tool that fits the job]] instead of trying to force the use of [[Obsidian]] where it doesn't make sense.
### Store xlsx in vault
[[xlsx]] is [[binary]], so not ideal for a [[git repository]].
- find a [[ASCII]] format we can use.
- or put in a [[gitignore|folder ignored by git]] and ~~write a script that syncs xlsx files with a [[data lake]].~~ Turns out [[Drive for desktop]] already syncs, so no need to write a script.
	- The sync solution is more complex but could be used for [[Google photos]] too, not just [[spreadsheets]].