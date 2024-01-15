Using Python outside Python's PATH, leads to annoying issues:
- the single `.py` file is not importable (without manually adding the path)
- since import logic doesn't work, there's no support for Python packages (a folder with multiple python files inside), only support for a single `.py` file.

Some apps load plugins dynamically, but don't add the folders to the sys path. So I've encountered unpredictable bugs because I assumed normal Python behavior.

offending apps:
- [[Maya plugin|Maya plugins]] can't use packages as a plugin. You need to put a separate package in the scripts folder, since the plugin folder is not included in the path.
- [[Pyblish]] plugins are not importable, and can't import files in the same folder.
- [[Blender addon|Blender addons]] are not included in the path. Sometimes a blender plugin has the same name as a python module in the path, so careful when adding plugins folders to the path.

[[unpythonic]]