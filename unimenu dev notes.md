
# DEV notes
- [ ] no docs on writing configs
- [ ] no docs on extending, adding apps

logic is config -> qt
a class in between enables use the [[unimenu]] loader, and use it for non qt menu-items
	config ->class inst -> qt menu
can now be reused in toolBrowser 
	config -> class -> qt buttons/widgets

quite a lot of work vs copy paste `_setup_menu_items` method 

## config learning
currently configs is in yaml.
- typing a command is akward, 
	- sometimes you need to use escape characters
	- and we need a pipe `|` char for multi-line commands.
- you cant shortcut to the python command definition in your IDE 
- a IDE might not realize it's used there so wont update references on a refactor.

much easier to just build our menu in a python file.
- [ ] TODO, can we still use multiple config files if we use this approach?

---

## TODO
- [ ] unimenu [[Blender]] teardown doesn't work correctly, creates 2 menus when re-enabled

- [ ] unimenu krita plugin, from [[krita plugin template]]
- [ ] unimenu [[Unreal]] plugin, from [[Unreal python plugin template]]
- [ ] unimenu [[Autodesk 3ds Max|max]] plugin, from [[3ds max plugin template]]
- [ ] unimenu [[Autodesk Maya|maya]] plugin, TODO maya template

- [ ] fix warnings unimenu [[Blender]] separator bug

[[dev notes]]