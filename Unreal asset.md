an asset in unreal is represented in python by [[unreal.assetData]]
e.g. [[unreal.AssetRegistry]] will be used to get them

An asset is a specific type of content within a [[unreal package]], such as a texture, mesh, material, or [[Unreal Blueprints Visual Scripting|Blueprint]]

Usually, to edit an asset, you need to load the [[unreal.Object|Object]] inside. Which is the instance of a class, e.g. a [[unreal.StaticMesh]] instance. (which inherits from Object)