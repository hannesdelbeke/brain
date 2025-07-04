class: unreal.AssetData
```python
unreal.AssetData(object_path='None', package_name='None', package_path='None', asset_name='None', asset_class='None')
```

kwargs
- object_path
- package_name
- package_path
- asset_name
- asset_class
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
