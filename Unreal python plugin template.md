A [[Unreal plugin]] template for [[pure Python]] plugins
https://github.com/hannesdelbeke/unreal-python-plugin-template

### Features
- this template is ready to plug & play, so just replace the code with your own.
- easy installation:
	1. Place the plugin in Unreal's `Plugins` folder
	2. Enable the plugin in Unreal 
		1. open `Edit > Plugins`
		2. search for `MyPlugin` (capital sensitive) and enable it
	3. Restart Unreal
- the repo includes code for a demo qt widget
- it auto installs dependencies on startup from `requirements.txt`, using [[py-pip]].
	- By default, it installs [[unreal-qt]], which installs [[PySide6]], because the demo widget uses it.
- [[Unreal - add menu with Python|adds the menu item]] `tools/myPlugin` to [[Unreal menu|Unreal's menu]] to launch the widget.
## TODO
- [ ] demo how to add a section in unreal's menu
- [ ] demo how to add an icon to the menu entry
- [ ] test on other OS
- Installing [[PySide]] to the project triggers import warnings for the jsons
	- I found [[Unreal control which folders to monitor for import|a manual editor fix]]
	- Can this be automated? e.g. on startup? Atm every user will run into this which is annoying.
- maybe we can make an installer: ([[plugget Unreal]] already kinda does this)
	- auto adds the plugin to the [[Unreal detect projects|most recent unreal project]]
	- auto enables plugin in project
	- now user only has to run the installer, and restart Unreal
## Reference
- [github.com/laycnc/UnrealExtenstionPluginsTemplates](https://github.com/laycnc/UnrealExtenstionPluginsTemplates) C++ Unreal plugin templates
- [tech-art.org thread](https://www.tech-artists.org/t/free-a-python-unreal-plugin-template/17995)
- unreal forum [thread](https://forums.unrealengine.com/t/made-a-python-plugin-template/1089878)
