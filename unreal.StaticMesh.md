inherits from [[unreal.StreamableRenderAsset]]

https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StaticMesh

## get_material
```python
mesh_asset.get_material(0) # returns first material
mesh_asset.get_material(99) # returns None if no material at index 99
```
## TODO figure out why this works
to find out how many materials are assigned to a mesh, you can count `get_material` in a loop untill it returns `None`
However get_material is supposed to take a LOD index which it doesnt
You can compare with static_materials, to find if any materials are unassigned. 
