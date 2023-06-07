---
sentiment:
- 5
sentiment-hash: 6123e894
sentiment-label:
- factual
tags:
- technical
---

```python
...
for mesh_asset_data in meshes:
    mesh_asset = mesh_asset_data.get_asset()  # load asset
    ...  # process your asset
    unreal.purge_object_references(mesh_asset)  # unload asset
```
