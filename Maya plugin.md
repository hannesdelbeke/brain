[[Autodesk Maya|Maya]] plugins are quite modular
- can be enabled or disabled per user
- manages it's own startup code


- [ ] how to control startup load order of plugins

- [ ] how to handle plugin dependencies?
  - best way so far is to avoid dependencies
	  - [ ] TODO sample
  - and use run_after_load / deferred load approach
	  - [ ] TODO sample

- use Maya's plugin manager to enable a plugin
- plugins can also be enabled with code

ideally a plugin is self contained
- adds itself to the menu
- and avoids dependencies that don't ship with Maya.
  but if we write more complex python code this is not reasonable, e.g. pymel, numpy, ...

[[Maya python]]