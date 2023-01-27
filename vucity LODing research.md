## LODing remeshing imposters

LODing is the act of removing (and sometimes subtly moving) existing verts from a mesh. attempting to retain all original mesh features such as the uv, normals, shape...

remeshing will create a brand new mesh, with a brand new uv, based on the original mesh, with the option to bake some original features into maps (bake normals into a normal map, bake texture into a diffuse map) remeshing can result in a much more optimized mesh, but comes with the cost of additional unique non tiling textures. it can be a great solution to [[level of detail|LOD]] a hero-mesh that is not using much tiling textures. the new maps could even be saved into the mipmaps of the original texture resulting in only a small memory increase. (this would however require a special shader to support this)

imposters is similar to remeshing, but bakes several textures from several angles. and uses a special shader to blend between them.

good LODs, remeshed meshes, and imposters should not be noticeable
quality of LOD doesn’t matter, only important thing is that it should be indistinguishable from the original mesh at the closest LOD distance it is meant to be used. so don’t worry if it looks bad closeup/

## pixel vs percentage LODing 

good LODing software can create a LOD, and compare a screenshot with the original mesh. and guarantee it will look pixel perfect the same. 
basic LODing software will instead create LODs based on a certain percentage of the original LOD. the issue with this is that not all meshes have the same density, so the same percentages wont work for all meshes. this means you ll need artists tweaking the numbers by hand. or you use a generic percentage for all meshes but then some meshes will LOD noticeably, and some will have a too high budget resulting in poor optimization.

the pixel based approach is the most accurate, but requires more work, and comes with the disadvantage that it is linked to pixels, so therefore is dependent on resolution. To properly use it, you either target your max resolution, or you have a dynamic approach.

#### example:

original mesh is 2000 triangles
on a 1920*1280 resolution, a perfect LOD, indistinguishable from the original mesh, takes up 128*128 pixels (10% of the height) and is 50 triangles
the same mesh at the same distance on a 4k resolution 3840*2160, is still 50 triangles, but now takes up 216*216 pixels. this is a much sharper resolution, so we will notice that the mesh is LODded.

  

we can either push the LOD activation further away, or we can increase the triangle budget for the LOD. both approaches will reduce optimization if we want to maintain perfect LODs. this is the cost of supporting LODing in higher resolution.

  

a first pass LODing approach is usually:
creates LODs with the following percentages 50 25 12.5 2 (total cost is about double memory)
with higher resolutions these days it is recommended to start LODs even higher, at 75 or 66 percent.
Then put these LODs in the game engine, push the distance until you cant tell the difference, and use a slightly further distance for all meshes. This will get the job done in most games, is straightforward, but not accurate.

  

a better but more advanced approach is the create the LODs based on pixelsize, targeting the maximum resolution, for a certain distance. so before we create LODs we decide when the LODs need to kick in. then we generate the LODs and implement them in [[Unity]]. however this means that when we go to a lower resolution, the LODs are not as optimized as they could be.
a solution to this would be to recalculate the LOD distances every time you change resolution.

  

let’s say i want a LOD to kick in when it’s smaller than 200 px, 100px, 20 px, 5px, 1px
a trick to decide the pixel sizes is to take a building, LOD it with 75% percent, then move it into the distance until you can’t tell the difference from the original. measure the size of the screenspace [[bounding box]] in pixels.
or you could just put in a few values, generate a quick test LOD and see if it is too much or enough reduction.

  

# notes

in [[Simplygon]] LODing is straightforward, most settings are self explanatory. 
keep in mind when you have the option to decide feature importance
(ex. silhouet, normals, uv distortion, ...)
you can not set all to highest. the feature importance is relative to other features. so if everything is highest you will have the same result as everything is medium.

  

if verts are touching each other but are not welded, it is possible for holes to be created in a LOD. to avoid this weld all verts before LODing a mesh. some LODing programs have support for avoiding or filling holes.

  

there often is a tickbox to enable vertex movement. this will result in a better LOD since it wont only remove verts, but might move the remaining verts to get a better overall result.

  

pay attention to the source of your LOD. Simplygon uses cascade LODing in some of their presets. this means it will create LOD 2 from LOD 1, and LOD 3 from LOD 2. this results in a much faster LOD generation. but often less accurate. 
 

a lot of games have a zoom function, binoculars, or special view mode. this often works by changing the field of view. quite often LOD systems do not support this and therefore you can see low quality LODs when zooming in.

LODs are activated over distance, but can also be activated when framerate drops, and when camera quickly spins around. due to the quick spinning a user would not notice the drop in quality. often the camera stutters when quickly moving since it has to load a lot of new content. briefly activating a lower level of LODs could improve performance in [[VuCity]].

# resources
- [Simplygon SDK 8.2 overview](https://documentation.simplygon.com/SimplygonSDK_8.3.33500.0/articles/starthere/productoverview.html) useful even if not using simplygon, explains lot’s of LODing related concepts
- [http://wiki.polycount.com/wiki/LOD](http://wiki.polycount.com/wiki/LOD)
