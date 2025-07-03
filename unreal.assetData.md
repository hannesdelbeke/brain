use [[unreal.AssetRegistry]] to get assetData
## get_asset() -> [[unreal.Object]]
returns the actual asset referenced in the assetData, e.g. the mesh
if it is loaded or loads the asset if it is unloaded then returns the result
```python
mesh_asset_data: unreal.assetData  # typehint
mesh_asset = mesh_asset_data.get_asset()
print(mesh_asset.static_materials)
```

