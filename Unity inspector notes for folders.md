I wrote a tool to add notes to folders in unity.
https://github.com/hannesdelbeke/unity-folder-notes

The advantage is that the notes live in the folder [[metadata]], instead of creating an additional file in your project. This means it's easier to keep everything in sync.
# todo
- [ ] support [[Unity search]].  
      e.g. for a [class Comments](https://gist.github.com/kurtdekker/e63690a1bfe9515d40d3f09a1470daba) you can search `t:comments`
- [ ] support [[URL]], [[wikilink]], [[Markdown]] [[HTML]]
      Rich text support could be interesting. 
      Maybe even support embedded images.
- support private / local / user notes vs project notes.
	- a dict with `{GUIDs: private notes}` in a gitignored folder.
	- ideally the GUIDs would not be textdata but unity metadata so they can auto update if GUID changes somehow.
	- this could be a separate tool
## alternatives
- Put a README textfile containing your notes in each [[folder]]. 
	- But you can't edit the notes in unity without a custom inspector/tool.
	- It adds an extra file, files could get outdated/out of sync.
- this can also be achieved with a gameobject in each folder, and [[Unity - add notes to gameobjects]]
	- But this also adds an extra file

[[Unity tool]]
[[my projects]]