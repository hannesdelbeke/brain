class: unreal.AssetData
```python
unreal.AssetData(object_path='None', package_name='None', package_path='None', asset_name='None', asset_class_path='None')
```

kwargs
- object_path: str - path to the [[unreal.Object|Object]], e.g. `/Game/folder/filename.filename`
- package_name: str - name of the [[unreal package|package]], e.g. `/Game/Textures/T_Foo.uasset``
- package_path: str - path to the [[unreal package|package]] e.g. ????
- asset_name: str - name of the asset, e.g. `StaticMesh` - this is not validated, it accepts any string
- asset_class_path: [[unreal.TopLevelAssetPath]] 
```python
mesh_class = unreal.StaticMesh.static_class() # <Object '/Script/Engine.StaticMesh' (0x000001EF6F294C68) Class 'Class'>
class_path = mesh_class.get_path_name()  # '/Script/Engine.StaticMesh'
top_lvl = unreal.TopLevelAssetPath(package_name = class_path) # <Struct 'TopLevelAssetPath' (0x00000987B9AA7BC0) {package_name: "/Script/Engine", asset_name: "StaticMesh"}>
unreal.AssetData(asset_class_path=top_lvl) # <Struct 'AssetData' (0x000009888C40B900) {package_name: "", package_path: "", asset_name: "", asset_class_path: {package_name: "/Script/Engine", asset_name: "StaticMesh"}}>
```
## attributes
[[unreal.assetData.asset_class|asset_class]] → [[unreal.Name|Name]]    
[[unreal.assetData.asset_name|asset_name]] → [[unreal.Name|Name]]    
[[unreal.assetData.get_asset|get_asset]]() → [[unreal.Object|Object]]  
[[unreal.assetData.get_class|get_class]]() → type([[unreal.Class|Class]])  
[[unreal.assetData.get_export_text_name|get_export_text_name]]() → [str](https://docs.python.org/2/library/functions.html#str)  
[[unreal.assetData.get_full_name|get_full_name]]() → [str](https://docs.python.org/2/library/functions.html#str)  
[[unreal.assetData.get_tag_value|get_tag_value]]() → [str](https://docs.python.org/2/library/functions.html#str) or None  
[[unreal.assetData.is_asset_loaded|is_asset_loaded]]() → [bool](https://docs.python.org/2/library/functions.html#bool)  
[[unreal.assetData.is_redirector|is_redirector]]() → [bool](https://docs.python.org/2/library/functions.html#bool)  
[[unreal.assetData.is_u_asset|is_u_asset]]() → [bool](https://docs.python.org/2/library/functions.html#bool)  
[[unreal.assetData.is_valid|is_valid]]() → [bool](https://docs.python.org/2/library/functions.html#bool)  
[[unreal.assetData.object_path|object_path]] → [[unreal.Name|Name]]  
[[unreal.assetData.package_name|package_name]] → [[unreal.Name|Name]]  
[[unreal.assetData.package_path|package_path]] → [[unreal.Name|Name]]  
[[unreal.assetData.to_soft_object_path|to_soft_object_path]]() → [[unreal.SoftObjectPath|SoftObjectPath]]  

## tips
use [[unreal.AssetRegistry]] to get assetData
