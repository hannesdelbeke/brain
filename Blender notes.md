seems the best solution would be native text
and add richtext support

## ideas
Any text datablock ending with '.md'


## native
- use the script editor to save text files in Blender files
	- can have multiple text nodes in the file
	- text nodes can be linked to frame nodes in [[Blender geometry nodes]] or shader nodes
		- see Node annotator plugin that extends on this.
	- no [[URL]] or richtext support
		- see Markdown plugins
			- https://github.com/TheDuckCow/blender-markdown
				- fixed code for new Blender, [download](https://blenderartists.org/uploads/short-url/3IGX1gxS8KmOf7xoEWWkgLzgPMd.py), from this [thread](https://blenderartists.org/t/markdown-in-blenders-text-editor-and-ui/1405542)
				  *Now it doesn’t support links, bold/italic, and the headers level are only shown by how many dots are placed below them. It’s very limited, but maybe someone with more knowledge than me can do something.*
## existing
- generic_note 
	- doesn't work for people who don't have the extension installed
	- archived
	- [repo](https://github.com/ly29/GenericNote) & [code](https://raw.githubusercontent.com/ly29/GenericNote/master/generic_note.py)
