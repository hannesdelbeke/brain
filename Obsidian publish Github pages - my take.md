## Goal
- single file to add to repo
- no settings or tweaking needed afterwards

## Challenges
- security limits options [[GitHub actions]] can do without a key from the settings

- rebuild site
	- rebuild whole site takes long / is wasted resources
		- rebuild only changes
	- rebuild changes results in duplicates when files are moved.
		- currently doesn't delete files
- for now always rebuild from scratch
	- doing this every commit vs on a time schedule

move notes to `doc`
move images to `iamges`
build site

see [[Obsidian web integration]] for my notes