To enable a [[Blender addons|Blender add-on]] with [[Python]], use
```python
import addon_utils
addon_utils.enable(addon_name)
```

Don't use this outdated code
```python
import bpy
bpy.ops.preferences.addon_enable(module=addon_name)
```
Since this will fail if the addon folder didn't exist on Blender start up.
It also uses operators which can cause issues when run from Qt.
