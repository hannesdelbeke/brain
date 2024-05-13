it'd be great if you could see why a blend file is so big in [[Blender]]
e.g. a single large texture or mesh, and which one.
a hidden animation

like this ([source](https://blender.community/c/rightclickselect/3pcbbc/?sorting=hot)) ![](https://d3a2gvihmbqfjo.cloudfront.net/f0/f0c3d66021b449eeb0b0cd8d227a6574/f0c3d66021b449eeb0b0cd8d227a6574.png)

[[Blender]] saves individual data blocks, which are readable with `bpy.data` but we can't get their size.
- can write to disk and read size after. but also takes dependencies (users) with it.
- see https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html
- linking and then unlinking the data-block might work ?
- pack & unpack might work https://docs.blender.org/manual/en/latest/files/blend/packed_data.html
- texture size is maybe available https://blender.community/c/rightclickselect/Czcbbc/?sorting=hot