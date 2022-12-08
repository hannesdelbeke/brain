# shader interoperability

Since shaders work different on different platforms, we cant make 1 shader to rule them all.

but an asset could be assigned a shader-ID e.g. `anime-1` , or `realistic-4` then on requesting the asset, we get the tag and load the matching shader

this empowers game devs to customize the shaders. e.g. Anime shaders in their game’s style.

you can’t load a shader just on it’s own. you always need to load it in a material.

## what is a material

a combination of

- shader
- texture
- parameters (e.g. specular strength, glow strength)
- mesh input (e.g. mesh normals, mesh UV)

## scenario 1

- realistic
- stylized

Both approaches could use a PBR shader. But they require different texture input: realistic textures vs stylized textures.

## scenario 2

- stylized
- anime style

stylized uses a PBR shader, anime style needs a custom shader

but we might be able to reuse textures between both styles. or maybe we don't want too.

## platforms
- web
- [[Unity]]
- [[Unreal]]
- [[GoDot]] 

a shader might work in unity 2019 but not in unity 2022

maintaining a library of premade shaders could be a lot of work.

i suggest to keep it to a minimum and instead rely on devs using the tags to support their own shaders.

<aside> ⚠️ a interoperable asset might fail to load the materials correctly on a different platform if there’s no matching shader for that platform AND that platform’s version

</aside>