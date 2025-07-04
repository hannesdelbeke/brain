## get_asset() -> [[unreal.Object]]
returns the actual asset referenced in the assetData, e.g. the mesh
if it is loaded or loads the asset if it is unloaded then returns the result
```python
mesh_asset_data: unreal.assetData
mesh_asset = mesh_asset_data.get_asset()
print(mesh_asset.static_materials)
```

when loading them in unreal, it doesn't unload them. To avoid running out of ram you can unload the object with [[unreal.purge_object_references]]
