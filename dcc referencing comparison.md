---
sentiment:
- 5
sentiment-hash: 252f968f
sentiment-label:
- factual
tags:
- technical
- work
---

reference a mesh, and modify the UV.
#### Supported
Only Maya supports editing UVs on a reference
- Maya stores them as reference edits in the working scene.
- You can inspect and manage these in the Reference Editor.
#### Not supported
Blender 
- you can override a mesh data block (verts, faces, UVs, vert colors, ...), but not just the UV.
- override works for properties (like location, visibility, modifiers, materials).
Unity
- the prefab system is similar to Blender's datablocks.
Unreal
- can't edit mesh UVs without scripting or USD

> [!NOTE]- More details for each dcc
> ### Unity
> - ✅ Prefab System = referencing with overrides.
> 	- Prefabs reference a base asset.
> 	- You can override components, materials, and transforms — but not mesh data (like UVs or geometry).
> - ❌ You can’t override UVs or vertex data in a prefab.
> - 🧩 Workaround: You could use a custom component to apply mesh modifications at runtime or clone and edit meshes via script.
> ### Unreal Engine
> - ✅ Supports referencing via Blueprints, instanced assets, and Data Layers.
> - 💡 Geometry Script (in UE5) can modify mesh data at runtime, including UVs.
> - ✅ USD integration supports referencing with overrides (materials, transforms, UVs).
> - ✳️ Unreal also supports hierarchical instancing and nanite instances, but they don't allow low-level UV edits directly on instances.
> ### Maya
> - ✅ File Referencing is one of its core features.
> 	- You can reference in an asset (e.g., a character rig or mesh).
> 	- ✅ You can override materials, UV sets, transforms, etc. non-destructively.
> - 🔒 Some things (like topology) can't be changed unless you do a reference edit or import it.
> - 🧩 You can use reference edits or deformer nodes (like UV editors or custom deltas) layered on top of a referenced mesh.
> ### Blender
> - ✅ Supports linked libraries (.blend file linking).
> - ❌ You cannot edit geometry or UVs of a linked object directly.
> - 🧩 Workaround:
> 	- Use a Proxy Object (older) or [Overrides](https://docs.blender.org/manual/en/latest/files/linked_libraries/library_overrides.html) (Blender 3+).
> 	- You can override materials, transforms, and certain properties — but not geometry/UVs.
> 	- To modify UVs, you must make it local, which duplicates the data — defeating your purpose.
>
