can be a simple tool 

- symlink
	- support dir presets
		- preset for plugin dir
		- preset for module dir
	1. browse to your plugin
	2. display command to manually run to symlink
- display which plugins are symlinked
- feature to unlink symlinks, or show command to run

### unreal repo plugins
[[Unreal]] plugin that lets you point to repos.
site package [[pth]]? or symlink?
pth is py only. we also want `.uplugin` files.
see [thread](https://forums.unrealengine.com/t/how-to-add-ue-plugin-search-paths-via-env-vars/477095/5):
- no plugin search path. 
- symlink can have issues in read only dir, e.g. program files
- rez can handle this. but technical hard.

same for [[Unity]]. symlink? and work w git / [[Perforce|p4]]
user only tools

same for [[Autodesk 3ds Max|max]], [[Autodesk Maya|maya]], [[Blender]], ...

also see [[Python packages editable install]]

[[tool idea]]