In code, package is the Outer of an [[unreal asset]]
packages types contain only one asset, which has the same name as the package

e.g. a Texture2D uasset package contains just a Texture2D object with the same name.
package path :` /Game/Textures/T_Foo.uasset`
asset name : `T_Foo`
fully qualified asset path :` /Game/Textures/T_Foo.T_Foo`

One exception is [[Unreal Blueprints Visual Scripting|Blueprint]] packages, where the “main” asset is the Blueprint itself (the thing you edit in editor), but its package also contains the generated class and CDO with slightly different names.

Create a package with CreatePackage, and use that as the Outer of the new asset you create. Then call SavePackage