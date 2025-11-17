If I download my [[Google Drive]] folder in my vault, i can [[wikilink GDrive files]] in my notes.

challenges:
- potential clashing file names with public notes
	- I expect this is rare since there are no [[Markdown]] files in my drive.
	- If it happens I can just rename the file.

### Walkthrough: How to embed GDrive folder in vault
- [x] can i use google drive as a subfolder in my [[Obsidian vault|vault]]?
- download gdrive [here](https://support.google.com/a/users/answer/13022292?hl=en)
- launch and sign in
- step 1
	- there's only the option to sync folders too drive, untick them all and don't use this.
- step 2 google photos
	- I get a warning for differences between [[sync with drive vs back up to photos]]
	- there's only an option to sync photo folders to photos/drive, untick all
- step 3 see drive files in explorer
	- defaults to stream mode, a [[virtual file system]], shows in explorer without taking up space.
		- it created a new hard drive `G:\`
		- to make drive files available offline rightclick - make available
	- you can set to `Mirror files` to [[file sync|sync]] drive to a folder in both ways (two-way sync) 
		- asks to select a folder where to mirror the whole drive too.
- add `google-drive/` to [[gitignore|.gitignore]] in my vault if you use [[git]]
- change drive settings to point to that folder.
	- seems i can also make it point to a streaming folder instead of `G:\` drive.
	 But when I do so Obsidian doesn't pick it up

Overall it seems to work well
I ran into some issues:

> [!BUG]- convert to jpg plugin deletes drive files
> The [[Obsidian paste img png to jpg]] plugin causes issues with gdrive syncing.
> The plugin is designed to convert a newly pasted jpg. It seems to do this by detecting new images, renaming and converting to jpg, and then moving the image.
> Moving an image out of drive deletes is from drive.
> And the images were being submitted to git by [[Obsidian plugin - Git]].
> 
> Things seem better after tweaking the settings of the [[Obsidian paste img png to jpg]] plugin
> - disable rename
> - disable move
> 
> I still got some weird bugs though.
> Uncaught (in promise) Error: ENOENT: no such file or directory, rename 
> C:\repos\pkm\google-drive\admin\work\archive\2016 Freejam\robocraft\robocraft wallpapers\ScreensRhino-4.jpg' ->
> 'C:\repos\pkm\google-drive\admin\work\archive\2016 Freejam\robocraft\robocraft wallpapers**NaNimage**\ScreensRhino-4.jpeg'

> [!warning]- slow autocomplete
> After integrating drive in [[my vault]], the [[Obsidian autocomplete]] is terribly slow. (5 seconds). I also rebuild the cache as a test, which might have slowed things.
> However, after fixing the previous image bugs and restarting it seems fine again.

this might be an option
also xslx files can be edited in google drive, so could use that instead of gsheet if i want to not be stuck in their custom file format.

see [[keep using google drive for my sheets in my vault]]