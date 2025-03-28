---
aliases:
  - Maya plugins
---

[[Autodesk Maya|Maya]] [[plugin]]s are quite modular
## Pros
- Plugins manage their own startup code, allowing you to avoid using `userSetup.py`, which always runs on startup.
- Plugins can be enabled or disabled per user, letting you toggle the startup code more easily compared to [[Maya module]]s.
## Cons
Maya plugins don't support:
- plugins can only be 1 `.py` file, because the plugin folder is [[Python outside Python path|not in the Python path]]
	- no modules or zip files
- [[dependencies]] on:
	- other Maya plugins
	- [[Python package]]
	You can depend on another package, e.g. `import numpy`, but installing the plugin won't auto install the `numpy` dependency.

You could instead use a [[Maya module]] to [[vendoring|vendor]] multiple Maya plugins or python packages.

## Notes
- Since plugins are not importable, they live in their own [[namespace]], and can have the same name as a importable Python module
- Maya plugin path is not added to sys.path
- invalid plugins without a init plugin method still show up in the plugin manager
- You could release 1 plugin, and 1 folder to the plugin path. And then edit `sys.path` to import the folder. But you might as well put that folder in `scripts` instead.
```
📁 plugins 
	🗒️ my_plugin.py
	📁 my_plugin_lib 
		🗒️ module1.py
		🗒️ module2.py
```

ideally a plugin is self contained
- it adds itself to the menu
- since a plugin is a single file, it aims to avoids dependencies that don't ship with Maya for easy manual install.
  but if we write more complex python code this is not reasonable, e.g. pymel, numpy, ...
## Extend ideas
- [ ] how to handle plugin dependencies?
  - best way so far is to avoid dependencies
	  - [ ] TODO sample
  - and use run_after_load / deferred load approach
	  - [ ] TODO sample
### Low prio
- [ ] how to control startup load order of plugins

## How to enable/disable a plugin
- use [[Maya plugin manager]] to enable a plugin
- or enable a plugin with code: [loadPlugin](https://download.autodesk.com/us/maya/2009help/commandspython/loadplugin.html) 
```python
import maya.cmds
maya.cmds.loadPlugin("my_plugin.py")
```

[[Maya Python]]
[[Maya tool]]