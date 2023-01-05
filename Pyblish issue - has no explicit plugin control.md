#### Pyblish has no explicit plugin control
Despite people requesting explicit control over plugin registration, there is only an implicit implementation.
You can't (easily) register a single plugin, (instead you register a folder with plugins.)
- [ ] todo link to proof / examples

### explicit
Sometimes you just want to only run plugins related to animations, or 3d environment.
### implicit
An all or nothing approach, always running all registered plugins.
Marcus believes a scene should be clean, so the tool can auto detect the correct type and activate the correct plugin. That's often not the case in game dev. Instead you are [[dumped in a messy project]] with hundreds of inconsistent scenes.


Some devs implemented their own explicit plugin registration: 
- [OpenPype](https://github.com/ynput/OpenPype/blob/1e7378c80fa027b49d06cd38967c8e6dbcdf5818/openpype/lib/plugin_tools.py#L207-L264)
- [Claudio](https://forums.pyblish.com/t/best-approach-to-registering-plugins-up-to-specified-order/724) 
- [Claudio again](https://forums.pyblish.com/t/pyblish-workflow-manifest/685/7) 
- my [[Pyblish plugin manager]]
- Jason (private)