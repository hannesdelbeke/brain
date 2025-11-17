## Context
This was written when I looked into [[link spreadsheets in Obsidian|how to link spreadsheets in Obsidian]].
Spreadsheets are [[xlsx]] files, which are binaries, not [[ASCII]] files. So any change to them uploads a whole new file to git, instead of just the [[file diff]].

cons of storing binaries in [[my vault]] on [[GitHub]] instead of on [[Google Drive]]
- data would not be easily accessible in the cloud if stored on Github. On GDrive, I can easily edit sheets in the cloud. E.g. github doesn't support pdf preview
- my [[GitHub repo]] would grow too large. 
	- Exceeding the [[GitHub repo size limit]] may result in customer support discontinuing hosting of my free repository.
	- A PITA to clone [[my vault]] on a new pc. (I could live with this)
	- If the vault gets too large I might get performance issues in [[Obsidian]]
	- A vault that's too large could prevent Obsidian working well on mobile

## Result
Since [[git]] isn't great for binaries, I'll [[keep using google drive for my sheets in my vault]].

### Notes
If you do store binaries on git, look into [[Git LFS]].

[[git repository]]
[[binary]]