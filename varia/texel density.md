---
aliases:
  - pixel density
  - texture density
---
Texel density is used to measure the density of the [[texel]]s on your mesh.
It's measured in **pixels per centimeter** _(2.56px/cm)_ or **pixels per meter** _(256px/m)_.

A uniform texel density results in a consistent look. When some areas have more detail than others, this is often because of an in-balanced texel density. 
## 1. Texel density within a mesh
When modelling a single mesh, try to keep a uniform scale for the UVs.

## 2. Texel density relative to other meshes
Once you import your mesh in a game engine, or render it in a scene next to other meshes, it's texel density also should be the same as the other meshes. 
Even if the texel density was consistent within the mesh, it still can clash with other meshes.

## TODO automatic calculate texel density score
[[calculate average texel density]]


## tools
- Free Blender addon https://mrven.gumroad.com/l/CEIOR
- Maya: Built in Texel Density addon with UV Toolkit.
- Max: Built in one with UV Editor
## references
- Texel density intro https://www.beyondextent.com/deep-dives/deepdive-texeldensity
- Texel Density and other texture theory (https://antodonnell.gumroad.com/l/rHAIO)
- All You Need to Know about Texel Density - Leonardo Lezzi (Texel Density: All you need to know HQ PDF)
- Texel Density : What It Means & How To Use It (https://youtu.be/Za5AIQXwqCs)
- Discussion: Talking Texel Density (https://youtu.be/ZL5nToMpjp8)
- What is Texel Density and How to Master it (https://youtu.be/5e6zvJqVqlA)
- What is Texel Density? - A Layman's guide. (https://www.artstation.com/artwork/qA1lDy)
- Understanding Texel Density (https://youtu.be/rWJRekLpXXU)
- How to find the right texel density for your asset (https://youtu.be/iL2iXizf9xM)