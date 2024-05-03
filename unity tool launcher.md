[[unity]] 
 [[tool launcher]]

unity menu's tend to contain a lot of files.
create a command browser that can search and run a command
plugin infrastructure

mode 1: pure commands
- recreate all default unity menu commands. e.g. open project settings
- custom commands. e.g. launch my editor tool (this can also be a menu command)

mode 2: right click commands in asset browser
right click shows a lot of commands in the project browser, to the point where it's overwhelming and fills the whole screen.
instead show an option that says "browse commands"
this opens a command browser with commands that run on that directory

option to add custom commands

- [[unity-editor-spotlight]]
	- browse assets & scenes
- dead 7y  [project](https://github.com/DarrenTsung/DTCommandPalette), good example of tool browser
	- Open Scenes
	- Select GameObjects in the Scene
	- Open Prefabs into a sandbox scene (requires [PrefabSandbox](https://github.com/DarrenTsung/DTPrefabSandbox))
	- 💖Run commands (any method with `[MethodCommand]` attribute can be run)
- dead 7y https://github.com/appetizermonster/Unity3D-QuickSearch
	- Search Assets
	- Search GameObjects on Active Scenes
	- 💖Execute Menu
	- Support Asset Dragging

### toolbars in unity
toolbars are more limited, since limited space, and require customization per user
samples:
- 6y sample toolbar, not generic https://github.com/baba-s/project-settings-toolbar
- 2y custom toolbar in unity. could use this to add a search bar for tools, assets, ... https://github.com/marijnz/unity-toolbar-extender
	- sample repo using this https://github.com/smkplus/CustomToolbar