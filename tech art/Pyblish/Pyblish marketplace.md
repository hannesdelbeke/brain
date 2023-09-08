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
 [![](https://camo.githubusercontent.com/e8c280cc9565beb5604096dcacf5c01f232eebe2c49f28510a3324310f405602/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f68616e6e657364656c62656b652f7079626c6973682d706c7567696e732d6d6179612d7175616c6974792d6173737572616e63653f636f6c6f723d67726579266c6162656c3d254532254144253930267374796c653d666c61742d737175617265) pyblish-plugins-maya-quality-assurance](https://github.com/hannesdelbeke/pyblish-plugins-maya-quality-assurance): 48 maya plugins [thread](https://forums.pyblish.com/t/collection-of-48-reusable-plugins-for-maya-validation/679) original [repo](https://github.com/robertjoosten/maya-quality-assurance)  
 [![](https://camo.githubusercontent.com/1f1c657c73c46c40a900d90bbb4a55c810ceb5e9da9092d2be91b51784eecf63/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f68616e6e657364656c62656b652f7079626c6973682d706c7567696e732d626c656e6465722d6c696e743f636f6c6f723d67726579266c6162656c3d254532254144253930267374796c653d666c61742d737175617265) pyblish-plugins-blender-lint](https://github.com/hannesdelbeke/pyblish-plugins-blender-lint): 7 blender plugins [thread](https://forums.pyblish.com/t/collection-of-7-generic-blender-plugins/693)  
 [![](https://camo.githubusercontent.com/dcdfabd2f895210418b819914693f01841c76de46c5416563915a3eb0e04abaa/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f68616e6e657364656c62656b652f7079626c6973682d706c7567696e732d6d6f64656c436865636b65723f636f6c6f723d67726579266c6162656c3d254532254144253930267374796c653d666c61742d737175617265) pyblish-plugins-modelChecker](https://github.com/hannesdelbeke/pyblish-plugins-modelChecker): (now behind source repo) 25 maya plugins [thread](https://forums.pyblish.com/t/collection-of-25-maya-mesh-validation-plugins/692)  
 [![](https://camo.githubusercontent.com/4c8ad72e8b3a17519a2b8dbdddf5d09649283db3cfefa10977c5092ed13d43a0/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f666b61696a756e2f6d6179615f7363656e655f636865636b3f636f6c6f723d67726579266c6162656c3d254532254144253930267374796c653d666c61742d737175617265) maya_scene_check](https://github.com/fkaijun/maya_scene_check): 15 maya plugins [thread](https://forums.pyblish.com/t/collection-of-15-reusable-plugins-for-maya-validation/680)  
 [![](https://camo.githubusercontent.com/269c07346fe55ab50a580593c2b308395b875adf044eacf16672290c15d5fad3/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f68616e6e657364656c62656b652f7079626c6973682d7265706f2d636f6c6c656374696f6e3f636f6c6f723d67726579266c6162656c3d254532254144253930267374796c653d666c61742d737175617265) pyblish repo collection](https://github.com/hannesdelbeke/pyblish-repo-collection): collection of links to usefull pyblish resources
 https://github.com/readyplayerme/pyblish-plugins blender plugins / actions
 https://github.com/readyplayerme/blender-asset-validator blender plugins / actions (DUPE)