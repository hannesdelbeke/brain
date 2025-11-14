Blender stores data in collections, see [bpy_prop_collection](https://docs.blender.org/api/current/bpy.types.bpy_prop_collection.html)

to get all meshes, returns a collection
```python
>>> bpy.data.meshes
<bpy_collection[1], BlendDataMeshes>
```

get a mesh from the collection
```python
>>> bpy.data.meshes[0]
bpy.data.meshes['Cube']
```

or retrieve the mesh data from the current selection
```python
>>> bpy.context.object.data
bpy.data.meshes['Cube']
```

a collection is like an array/dict that stores the meshes 
```python
>>> [x for x in bpy.data.meshes]
[bpy.data.meshes['Cube']]
```

prints collection dict keys
```python
>>> bpy.data.meshes.keys()
['Cube']
```

[[Blender scripting]]
[[Blender snippet]]