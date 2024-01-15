---
aliases:
  - Maya plugins
---

[[Autodesk Maya|Maya]] [[plugin]]s are quite [[modular]], and my favorite way of packaging [[Maya tool]]s.
## Pros
- Plugins manage their own startup code, allowing you to avoid using `userSetup.py`, which always runs on startup.
- Plugins can be enabled or disabled per user, letting you toggle the startup code more easily compared to [[Maya module]]s.
## Cons
Maya plugins don't support:
- A plugin can only be a single `.py` file, because the plugin folder is [[Python files outside a Python path|not in the Python path]].
  It can't be a [[Python package]], or a zip file.
  If you want to include additional files, I recommend to distribute them as a [[Python module]] in the `scripts` folder, and import them from the plugin. You can also set them as a dependency, see [[Maya plugin template]].
- There is no native support for [[dependencies]] on:
	- other Maya plugins. (However using [[plugget]] this is possible)
	- [[Python package]]s (a custom solution can be seen in [[Maya plugin template]])
	You can depend on another package, e.g. `import numpy`, but installing the plugin won't auto install the `numpy` dependency.

Instead, you can use a [[Maya module]] to [[vendoring|vendor]] multiple Maya plugins or python packages.
However, I recommend to not use more than 1 Maya module per project, and package your tools in plugins instead.

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
- [x] how to handle plugin dependencies?
	- see [[Plugins are more modular than modules]]
	- [[plugget - create a self-installing plugin]]
  - if you depend on other plugins, you can use run_after_load / deferred load to ensure they are available?
	  - [ ] TODO sample
### Low prio
- [ ] how to control startup load order of plugins


[[Maya - how to enable-disable plugins]]

