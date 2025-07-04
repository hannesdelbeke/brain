```python
...
for mesh_asset_data in meshes:
    mesh_asset = mesh_asset_data.get_asset()  # load asset
    ...  # process your asset
    unreal.purge_object_references(mesh_asset)  # unload asset
```