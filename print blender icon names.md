Print all [[Blender]] icon names from [icon items](https://docs.blender.org/api/current/bpy_types_enum_items/icon_items.html)
```python
# from ...\Blender 3.2\3.2\scripts\addons\development_icon_get.py
import bpy
prop = bpy.types.UILayout.bl_rna.functions["prop"]
icons = prop.parameters["icon"].enum_items.keys()
print(icons)
```

[[Blender Python]]
[[icon]]