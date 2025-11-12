## Context
Many plugins are just light [[wrapper plugin|wrapper plugins]] around a [[Python package]]: some [[examples of wrapper plugins|examples]]
## Goal
Can we create a unified solution to avoid a new [[repository|repo]] & [[plugin]] for each tool?

Pure command plugget packages:
- since it's a plugget package, it handles dependency installation
- using plugget avoids duplicating vendored install code in each plugin. 
- if the command is simple enough, it could avoid the need for a plugin at all. 
> [!example]- vendored install code example
> e.g. currently plugget blender addon, and plugget unreal, and plugget maya plugin all have their own code to make the install process a 1 click process. auto installing dependencies for you. Since the user doesn't has plugget and it's dependencies installed when they install plugget, this needs to be all hardcoded in the plugin, resulting in a lot of duplicate code (cleanly install dependencies) that already exists in the plugget app actions.

However if you need custom dcc code like adding to menu, dockable in Maya, parent to qt, it might still be worth creating a plugin, or a [[Python module]] as dependency.
## brainstorm
There's some overlap with 
- [[unimenu]], since we launch a simple command from the menu.
- [[buttonizer]] also launches a simple command
- [[plugget]] has [[plugget action|plugget actions]] which are simple commands, and [[plugget install action]]

- we could [[plugget - create wrapper plugins on install|dynamically wrap code in plugins]]
- If it's just an action we could even use only plugget, without creating a plugin
	- [x] plugget installs a plugget package.
	- [x] Add support to run custom [[plugget action|plugget actions]] from [[plugget qt|the plugget GUI]] 
	- [x] Add default app actions: actions for a certain dcc that apply to all [[plugget package|plugget packages]]
	- [x] create a test package, that has no installable repo, but has an action (the script) [[expose a python tool in plugget without wrapping it]]
	- [ ] Create a [[plugget - action browser]] for better UX
- [ ] A nice thing about plugins is that they can run startup code, can we also do this without plugins? e.g. on startup we run the plugget package startup code. See [[Plugget - run startup code without a plugin]]
- [ ] Plugins also are easy to enable/disable. Plugget packages are easy to (un)install, so we kinda already have this logic. Maybe add support to keep it installed but disabled.

[[wrapping]]