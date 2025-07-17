
- `BLENDER_SYSTEM_EXTENSIONS` points to a folder of [[Blender extension]]s 
  (see [[Blender environment variables]])
- default user folder is `C:\Users\H\AppData\Roaming\Blender Foundation\Blender\4.3\extensions\blender_org\jiggle_physics`
- it contains non zip files, despite docs saying extensions should be build as zip

## test setting up a local extension for development
- set the env var `BLENDER_SYSTEM_EXTENSIONS` to `C:/folder`
- create a folder `C:/folder/system` inside
- copied the jiggle physics extension in there `C:/folder/system/jiggle_physics`
- rename folder, manifest id, manifest name
- it now shows a disabled extension in Blender with the new name, enable it.

