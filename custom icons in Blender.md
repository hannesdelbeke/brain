by default Blender only supports icons in the [icon items](https://docs.blender.org/api/current/bpy_types_enum_items/icon_items.html) enum 

Operator takes 2 kwargs (e.g. see [the UILayout docs](https://docs.blender.org/api/current/bpy.types.UILayout.html))
- `icon_value` is the icon ID
- `icon` is the icon name from the default icon items enum

see [previews docs](https://docs.blender.org/api/current/bpy.utils.previews.html)
```python
self.layout.operator(id_name, icon_value=icon_name)  # icon ID (int)
self.layout.operator(id_name, icon=icon_name)  # icon enum name (string)
```

```python
from bpy.utils import previews

preview_collection = previews.new()
icon = preview_collection.load(
    name="icon_name", 
    path="/custom/icon/path.png", 
    path_type='IMAGE'
)  # load returns the icon

icon_ID = icon.icon_id
icon = preview_collection["icon_name"]  # icon can be loaded by name
```

