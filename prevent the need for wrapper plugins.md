## Context
Many plugins are just light [[wrapper plugin|wrapper plugins]] around a [[Python package]]: some [[examples of wrapper plugins|examples]]
## Goal
Can we create a unified solution to avoid a new [[repository|repo]] & [[plugin]] for each tool?
## brainstorm
There's some overlap with 
- [[unimenu]], since we launch a simple command from the menu.
- [[buttonizer]] also launches a simple command
- [[plugget]] has [[plugget action|plugget actions]] which are simple commands, and [[plugget install action]]

A [[plugget install action]] could create an empty plugin, and hookup a simple show command.
If it's just an action we could even use only plugget, without creating a plugin:
- [x] plugget installs a plugget package.
- then on startup runs the plugget package startup code (if any). 
  see [[Plugget - run startup code without a plugin]]
- [x] Add support to run custom [[plugget action|plugget actions]] from [[plugget qt|the plugget GUI]] 

This would handle clean dependency install, and avoid duplicating vendored install code in each plugin. It would avoid the need for a plugin at all.
> [!example]- vendored install code example
> e.g. currently plugget blender addon, and plugget unreal, and plugget maya plugin all have their own code to make the install process a 1 click process. auto installing dependencies for you. Since the user doesn't has plugget and it's dependencies installed when they install plugget, this needs to be all hardcoded in the plugin, resulting in a lot of duplicate code (cleanly install dependencies) that already exists in the plugget app actions.

TODO
- [ ] run registered package actions on startup, perhaps not in plugget to avoid plugget becoming the env manager?
- [x] support package actions + default app actions
- [x] create a test package, that is not installable, but has an action (the script)
      I kind of ended up doing this in plugget: [[expose a python tool in plugget without wrapping it]]