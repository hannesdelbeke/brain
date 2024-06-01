[[Autodesk Maya|Maya]] plugins are quite modular
- They manage their own startup code, allowing you to avoid using `userSetup.py`, which always runs on startup.
- Plugins can be enabled or disabled per user, letting you toggle the startup code more easily compared to [[Maya module]]s.
## Cons
Maya plugins don't support:

- [[dependencies]] on:
	- other Maya plugins
	- [[Python package]]
	You can depend on another package, e.g. `import numpy`, but installing the plugin won't auto install the `numpy` dependency.

You could instead use a [[Maya module]] to [[vendoring|vendor]] multiple Maya plugins or python packages.****
## Extend ideas
- [ ] how to control startup load order of plugins

- [ ] how to handle plugin dependencies?
  - best way so far is to avoid dependencies
	  - [ ] TODO sample
  - and use run_after_load / deferred load approach
	  - [ ] TODO sample

ideally a plugin is self contained
- adds itself to the menu
- and avoids dependencies that don't ship with Maya.
  but if we write more complex python code this is not reasonable, e.g. pymel, numpy, ...

## How to enable/disable a plugin
- use [[Maya plugin manager]] to enable a plugin
- or enable a plugin with code: [loadPlugin](https://download.autodesk.com/us/maya/2009help/commandspython/loadplugin.html) 
```python
import maya.cmds
maya.cmds.loadPlugin("my_plugin.py")
```

[[Maya Python]]