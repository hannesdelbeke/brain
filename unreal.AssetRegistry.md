---
sentiment:
- 5
sentiment-hash: efc89d9f
sentiment-label:
- factual
tags:
- technical
---

get the asset registry
```python
import unreal

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
```

get all [[unreal.assetData]] for every asset in game
```python
assets = asset_registry.get_assets_by_path('/Game/', recursive=True)
```
