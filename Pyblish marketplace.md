how would you make a marketplace for [[Pyblish]]

- a python module that manages plugin detection, and installation/discovery

## distribution
- ~~download python file from the web., no need for packaging each file IMO~~
- plugins might have dependencies, e.g. another module, install as py-module solves that.
- a central repo that tracks plugins (overlap with [[plugget]])
	- [ ] make a Pyblish folder in plugget-pkgs 
- save plugin to a folder in e.g. `local/pyblish`
- [ ] create Plugget install action for Pyblish
## installation
- a UI to browse plugins, their instructions, etc. 
	- click on plugin (pack) to install it, or read description.
- [ ] reuse  [[plugget qt ui]] 
- [ ] create a Pyblish manager, all it has to do is discover plugins from `local/pyblish`
## config
mix and match plugins, with the [pyblish-config](https://github.com/hannesdelbeke/pyblish-config): create a config for your Pyblish pipeline  

Pyblish plugins
- [pyblish-plugins-maya-quality-assurance](https://github.com/hannesdelbeke/pyblish-plugins-maya-quality-assurance): 48 maya plugins [thread](https://forums.pyblish.com/t/collection-of-48-reusable-plugins-for-maya-validation/679) original [repo](https://github.com/robertjoosten/maya-quality-assurance)  
- [pyblish-plugins-blender-lint](https://github.com/hannesdelbeke/pyblish-plugins-blender-lint): 7 blender plugins [thread](https://forums.pyblish.com/t/collection-of-7-generic-blender-plugins/693)  
- [pyblish-plugins-modelChecker](https://github.com/hannesdelbeke/pyblish-plugins-modelChecker): (now behind source repo) 25 maya plugins [thread](https://forums.pyblish.com/t/collection-of-25-maya-mesh-validation-plugins/692)  
- [maya_scene_check](https://github.com/fkaijun/maya_scene_check): 15 maya plugins [thread](https://forums.pyblish.com/t/collection-of-15-reusable-plugins-for-maya-validation/680)  
- [pyblish repo collection](https://github.com/hannesdelbeke/pyblish-repo-collection): collection of links to usefull pyblish resources
- https://github.com/readyplayerme/pyblish-plugins blender plugins / actions
- https://github.com/readyplayerme/blender-asset-validator blender plugins / actions (DUPE)