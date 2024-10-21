If you try export FBX while the fbx plugin is not active in Maya, you'll get the Error:

> [!ERROR] 
> pymel.core.language.MelUnknownProcedureError: Error during execution of MEL script: line 1: Cannot find procedure "FBXLoadExportPresetFile".

To prevent this, load the FBX Plugin by code, then check if it loaded successfully.

TODO code snippet
```python
import maya.cmds as cmds

plugin_name = 'fbxmaya'

# Load the FBX plugin if it's not already loaded
is_loaded = cmds.pluginInfo(plugin_name, query=True, loaded=True)
if not is_loaded:
	cmds.loadPlugin(plugin_name)

# Check if the plugin is loaded
is_loaded = cmds.pluginInfo(plugin_name, query=True, loaded=True)
print(f"Is the FBX plugin loaded? {is_loaded}")
```

A workaround is to manually enable the fbx plugin in the [[Maya plugin manager]] 

[[dependencies]] between 2 [[Maya plugin|Maya plugins]]
