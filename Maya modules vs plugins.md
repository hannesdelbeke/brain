## Maya modules vs plugins
**IMO, If you only have a few files, use a plugin for a simpler installation & distribution.**

Compared to [[Maya plugin|Maya plugins]], [[Maya module|Maya modules]] let you ship more advanced solutions, containing scripts, icons, plugins, textures, ... and modify your environment without a need to write any code. 
A module is a pre-made folder structure mirroring the Maya project folder structure, enabling you to extend Maya without having to manually code more complex parts such as extending the path, modifying the environment, or load different settings based on the version of Maya, etc. Instead the user can just drag and drop their files in a folder, and hook it up in the module config.

The advantage of plugins is they can be disabled or enabled per user. A module is always fully enabled by default unless you modify the config.

similar to [[Plugins are more modular than modules]]