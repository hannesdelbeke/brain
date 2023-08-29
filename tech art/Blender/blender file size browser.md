it'd be great if you could see why a blend file is so big.
like this ([source](https://blender.community/c/rightclickselect/3pcbbc/?sorting=hot)) ![](https://d3a2gvihmbqfjo.cloudfront.net/f0/f0c3d66021b449eeb0b0cd8d227a6574/f0c3d66021b449eeb0b0cd8d227a6574.png)

blender saves individual data blocks.
access with `bpy.data` but can't read size.
- can write to disk and read size after. but also takes dependencies (users) with it.