execute console (run from script editor)
```python
import bpy

from bpy import context
window = context.window_manager.windows[0]
screen = window.screen
for area in screen.areas:
    if area.type == 'CONSOLE':
        with context.temp_override(window=window, area=area):
            bpy.ops.console.execute()
```

[console source code](https://github.com/blender/blender/blob/3735a4d104936ecd13dc8163d611c499d96a3046/scripts/modules/console_python.py#L37)
[[Blender Python]]
[[Python snippet]]