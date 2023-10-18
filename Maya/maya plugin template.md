
created a new plugin & module template https://github.com/hannesdelbeke/maya-plugin-template

Since Python modules are usually developed in their own repo, [[vendoring]] Python modules in the scripts folder results in duplicate outdated data.
- [ ] TODO figure out a nice approach for this with requirements

### existing Maya templates
- https://github.com/FXTD-ODYSSEY/Maya-UIBot plugin & module template, with .ui loader
	- module with . (local path)
	- module installer
	- plugin
	- parsers in [config](https://github.com/FXTD-ODYSSEY/Maya-UIBot/tree/main/UIBot/config):
		- tool entry
		- shelf entry
		- menu entry
		- status entry? (think not yet implemented)
	- MIT license
	- pure [[Python]]
	- Qt loader
	- 🔻usersetup.py
- https://github.com/tbttfox/mayaPluginTemplate 
	- module
	- 🔻contains both Python & C++
	- 🔻complex. contains rig code etc. 
	- i like the replace project name script.
- https://github.com/robertjoosten/maya-module-installer maya module template, no plugin
	- fix [fork](https://github.com/robertjoosten/maya-module-installer/commit/690d92e539a0775585975285b7031b077fa94ca0), add support for . path 
	- MIT license
	- 🔻no plugin