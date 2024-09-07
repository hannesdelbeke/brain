[[Jupyter Notebook]] and [[Blender]]

2 options

## Notebook controls a local Blender instance
- have a notebook or google collab, that creates a link to a local Blender instance.
- then in a code cell in your notebook you can run
```python
import bpy
bpy.ops.mesh.primitive_cube_add()
```
which creates a cube in your open Blender instance.

You could have a notebook on a website or google collab, just go to a URL.
Open a local Blender, and follow along with an interactive tutorial. Just run the codecells and see the output in Blender. 
## Notebook in Blender
somehow load notebooks directly in Blender.
- The user downloads a notebook.
- they load it in their Blender notebook addon.
- a UI shows the notebook inside of Blender
- they can run cells etc, just like usual.

A user can follow along with an interactive tutorial. 