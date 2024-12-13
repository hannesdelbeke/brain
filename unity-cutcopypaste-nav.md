i mainly use this tool to navigate between previously selected Unity assets.

## Details
- github [repo](https://github.com/wappenull/unity-cutcopypaste-nav) for a [[Unity tool]] with navigation: back&  forward, and up & down folder.
  Tested & works
	- [ ] ideal would be, instead of alt arrow, use mouse back button
	      might be able to do this with extra script? or change unity preferences
	  - doesn't seem to use unity shortcuts, but implemented it's own shortcut manager.
## Features
### copy
- [x] Allows you to Copy (Ctrl+C) Cut (Ctrl+X) Paste (Crtl+V) in Unity project (file) view. (aka project explorer window)
	- this is now a native Unity feature
	- it would be cool if i can copy something in (windows) explorer, e.g. a image. and paste it in unity project view.
### navigate
- [ ] Allows you to do Windows explorer-like navigation, Back (Alt+Left) Forward (Alt+Right) Up one level (Alt+Up) in Unity project (file) view.
based on [[unity-history-window]], which seems to have way more starts and users.
let's move development to there and add mouse support

[[Unity tool]]