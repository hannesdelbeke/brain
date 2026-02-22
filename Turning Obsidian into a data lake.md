---
views: 1
---
new notes
- [[wikilink GDrive files]]
	- [ ] [[link spreadsheets in Obsidian]]
- [ ] wikilink google photos

I used to store my data in [[cloud storage]], now I mostly use my [[Obsidian vault]] in a  [[GitHub repo]].

> [!NOTE]- Compare pros & cons
> | Obsidian<br>.                                                                                                  | cloud storage                                                                                  |
> | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
> | I can download & backup my vault data with 1 git command.<br>.                                                 | not backed up, only in cloud                                                                   |
> | If [[GitHub]] goes down, I can still access my data.<br>.                                                      | not local. When [[2020-08 Gdrive went down\|GDrive went down]] I couldn't access my documents. |
> | can easily link notes & data. Linking adds a lot of value to my life, so I want to [[use more links in life]]. | Can't link in Obsidian with [[Obsidian autocomplete]], it's more time consuming to link       |

Because of the pros of using [[Obsidian]], I want to move all my data to a central place. 
- I'm mostly interested in the power of [[link|linking]], the [[Obsidian autocomplete]] that shows when I type `[[`. 
	- imagine i link to a script from a personal project, and clicking the link opens it up in my code editor.
		- but how does it know to open a single file, or load a whole project?
		- what would the UX look like for other things, e.g. "memories" [[TODO localize instagram memory posts]].

[[2026-02-19 Obsidian auto complete app URI]]

bonus points if my IDE also can do this in the comments section.
but in future i might not even read comments since AI coding is taking over.

- Secondly, I want to [[backup]] my data. My dropbox and gdrive aren't backed up.
	- [x] I backed up [[Google Drive]] by [[embed Google Drive folder in Obsidian]]
	- There's not much left I care about on my [[dropbox]], i moved some game repos on [[github]]
	- [ ] still need to back up many photos. Some live on [[Google Photos]] only so no backup.
	- [ ] what about my old hard drives from (pre) uni? haven't touched them since.

[[git repo is not great for binaries]]

most data is 
- text
- excel sheets
- csv
- pdf
- image
- code

It makes sense for code to live in its own repos. So I need a solution that has repos in repos, like [[git subtree]] or [[git submodule]], or a script that [[file sync|syncs]] to a [[gitignore]] folder.

however it'd still be good to have a command in a backup note i can run to easily [[backup]] all repos locally, including repos I don't own but have access to like [[BQt]]

### drive
to move over my drive I need to 
- keep folder structure
- or create a note folder structure with links
- I don't want to include all my files in my vault since it'd increase clone time, however clone time is a one of thing.
	- I can put in a submodule, so I can clone without my data
	- can I use [[VFSForGit|Virtual File System for Git]] to get files on the fly?
	- I could create multiple vaults

ideally the solutions for the binaries on drive is the same as the solution for my [[Google Photos]] backup.

[[embed Google Drive folder in Obsidian]]
## insta 

integrate instagram into my data lake:
- [[TODO link contacts to photos and memories]]
- [[TODO localize instagram memory posts]]
- [[2025 - Instagram as a diary]]
### tags
[[data lake]]
