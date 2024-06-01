Maya modules are self contained Maya environments. Enable easy [[file distribution|distribution]] with relative paths in the module config.

They can:
- modify [[environment variable]]s:
	- custom [[maya plugin path]]s
	- custom [[site packages]] paths
	- ...
- [[vendoring]] assets:
	- [[Maya plugin]]s
	- [[Python package]]s
	- [[icon]]s
## Maya modules vs plugins
**IMO, If you only have a few files, use a plugin for a simpler installation & distribution.**

Compared to plugins, modules let you ship more advanced solutions, containing scripts, icons, plugins, textures, ... and modify your environment without a need to write any code. 
A module is a pre-made folder structure mirroring the Maya project folder structure, enabling you to extend Maya without having to manually code more complex parts such as extending the path, modifying the environment, or load different settings based on the version of Maya, etc. Instead the user can just drag and drop their files in a folder, and hook it up in the module config.

The advantage of plugins is they can be disabled or enabled per user. A module is always fully enabled by default unless you modify the config.

 [[Maya Python]]
