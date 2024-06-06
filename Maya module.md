Maya modules are self contained Maya environments. Enable easy [[file distribution|distribution]] with relative paths in the module config.

They can:
- modify [[environment variable]]s:
	- custom [[maya plugin path]]s
	- custom [[site packages]] paths
	- ...
- [[vendoring]] assets:
	- [[Maya plugin]]s
	- [[Python package]]s,  [[Maya Python]]
	- [[icon]]s
## Startup
### usersetup
If you have a maya module, it can have its own [[usersetup]] file (mel or python) that should excute after the main ones
### load / unload
An undocumented feature
`MODULENAME_load.py` runs on startup.
it bypasses checksum on startup.

you can also run a `_unload` ? how is this hooked up.

This was added to support the Autodesk exchange store, see [[Distributing plug-ins & files on Maya (and 3ds Max) - 2013]]

- [thread on `_load`](https://discourse.techart.online/t/alternative-to-usersetup-mel-in-maya-modules/14375/9)