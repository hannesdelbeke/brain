load all assets, then check if the first asset has auto compute LOD
```python
import unreal

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
assets = asset_registry.get_assets_by_path('/Game/', recursive=True)

meshes = [asset for asset in assets if "StaticMesh"  in str(asset.asset_class_path.asset_name) ]

mesh_asset_data = meshes[0]
mesh_asset = mesh_asset_data.get_asset()

mesh_asset.is_lod_screen_size_auto_computed() 

```
[[Unreal Python snippet]]