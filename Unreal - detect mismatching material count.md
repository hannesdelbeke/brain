sometimes meshes in unreal have more materials than they use
this code detects affected assets. It's not cleaned up so read it before you run it.
it also doesn't unload assets so you'll run out of ram and unreal will crash
you can use [[unreal.purge_object_references]] for this (untested)


```python
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
assets = asset_registry.get_assets_by_path('/Game/', recursive=True)

# if isinstance(mesh, unreal.StaticMesh):
meshes = [asset for asset in assets if "StaticMesh"  in str(asset.asset_class_path.asset_name) ]

len(meshes) # 309583

# i case of crash, find index where left off#
for i, mesh in enumerate(meshes):
    if "/58B8247D/mesh_name" in str(mesh): print(i)

mesh_asset_data = meshes[0] # type assetData
mesh_asset = mesh_asset_data.get_asset()

# count material slots, AFAIK on lod
mesh_asset.get_material(0) # returns first material
mesh_asset.get_material(99) # returns None

# static_materials slots
mesh_asset.static_materials

def mismatch_materials(mesh_asset):
    lod_mats = 0
    i = 0
    while i<99:
        try:
            mat = mesh_asset.get_material(i)
            if not mat:
                break
        except:
            return
        i += 1

    if len(mesh_asset.static_materials) != i:
        print(mesh_asset)

for mesh_asset_data in meshes[12331:]:
    mesh_asset = mesh_asset_data.get_asset()
    mismatch_materials(mesh_asset)
```
[[Unreal Python snippet]]
[[unreal.assetData]]
[[unreal.AssetRegistry]]