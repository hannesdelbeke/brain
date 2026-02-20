### No use for disabling plugins
Disabling a [[Autodesk 3ds Max|3ds max]] plugin doesn't delete its [[menu]] in max (e.g. `civil view`).
Whereas maya and blender have option to run code on disable, cleaning up the menu. There's no callback or hook on disabling a plugin.

Disabled plugins re enable on max restart. I don't know when someone can disable a plugin. It seems they are all loaded on startup.

### Not for me
Since even [[Claude Code]] is struggling to create a basic plugin that makes a menu on startup. I will stick to the non plugin setup.

### References
I only once used the modern plugin framework: for [[Max dark script editor listener]], since it's required to release on the [[Autodesk Exchange Store]].

Also check out [[Distributing plug-ins & files on Maya (and 3ds Max) - 2013]] for more info on the package format.


[[3ds max tool]]