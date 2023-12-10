common source control mistakes
- not using source control
- versioning inside source control. e.g.  uploading a v1, v2, v3 to a [[git]] or [[perforce]] repo
- not uploading source files but release or compressed files, e.g. [this](https://github.com/CydoniaValley/ue_collider_tool/issues/1)
- not locking a file
  when several people work on a project simultaneously , you will at points have conflicts. Code can often be merged, but you can't merge raw data like textures, meshes, game-files.
  To prevent this, you can use a file locking system. Both git and perforce support this.
- relying on auto merge.
  there are several tools and apps out there that attempt to auto merge your code in case of a conflict. e.g. [unity smart merge](https://docs.unity3d.com/Manual/SmartMerge.html), beyond compare, ...
  Do not blindly trust the result and always manually check & test the result. It often messes up.
  