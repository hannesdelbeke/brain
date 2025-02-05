---
aliases:
  - content browser
  - asset browser
  - asset manager
---

An asset manager is a tool to visually browse [[asset|assets]].
Useful when a studio has thousands of assets, and the assets do not have a thumbnail, or are hard to search in explorer.

- a folder with 1000 `.fbx` files, unclear naming, and no thumbnails
- a folder with subfolders containing various files each. hiding the name and preview image

An asset browser speeds up finding the right asset instantly, by providing a search and visual preview.

suggested features
- [[search bar]]
- [[favorite]]
- easy load / import / open file
- [[categorize]]
- [[thumbnail]]
- add content root paths, or add single asset path
## Blender
- [[Blender]] has a [file browser](https://docs.blender.org/manual/en/latest/editors/file_browser.html), which is basic and similar to the experience in explorer.
- Blender has an [asset browser](https://docs.blender.org/manual/en/latest/editors/asset_browser.html), which is slow. It needs to load all the `.blend` files to generate the thumbnails. And it requires assets to be marked as an asset in the blend file.
- Various 3rd party asset browser addons exist, mostly as [[Blender  N-Panel|N-panel]] feeling a bit clunky.

- The perfect asset manager would 
	- support thumbnails for a huge amount of files, near instant.

Maya sample 
- https://github.com/leixingyu/assetManager
- ![](https://camo.githubusercontent.com/006e0040774a22ec0f66a59adadde3a47d6bbf801b1249b9ab9a004e9cc463d6/68747470733a2f2f692e696d6775722e636f6d2f473455644479342e706e67)