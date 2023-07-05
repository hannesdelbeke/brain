
- [ ] these are research notes that could use a cleanup #todo

when using `python -m pip` , certain paths that are added dynamically on blender startup, are ignored.
e.g. the `appdata/roaming/.../addons` path is not exposed to [[python pip|pip]], since it's dynamically added on Blender startup.

> [!print paths in blender]-
> ```python
> import site
> site.getsitepackages()
> ['C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\python', 'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\python\\lib\\site-packages']
> site.getusersitepackages()
> 'C:\\Users\\user\\AppData\\Roaming\\Python\\Python310\\site-packages'
> 
> import sys
> import pprint
> pprint.pp(sys.path)
> ['C:\\Users\\user\\AppData\\Roaming\\Blender Foundation\\Blender\\3.2\\scripts\\modules',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts\\startup',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts\\modules',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\python310.zip',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\python\\DLLs',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\python\\lib',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\python\\bin',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\python',
>  'C:\\Program Files\\Blender Foundation\\Blender '
>  '3.2\\3.2\\python\\lib\\site-packages',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts\\freestyle\\modules',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts\\addons\\modules',
>  'C:\\Users\\user\\AppData\\Roaming\\Blender Foundation\\Blender\\3.2\\scripts\\addons\\modules',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts\\addons',
>  'C:\\Users\\user\\AppData\\Roaming\\Blender Foundation\\Blender\\3.2\\scripts\\addons',
>  'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts\\addons_contrib']
> ```
> 


### ❌ pass the env containing `sys.paths`
[pass the ENV](https://stackoverflow.com/questions/2231227/python-subprocess-popen-with-a-modified-environment) to the subprocess
passing the current env doesn't work `subprocess.run(command, env=os.environ.copy())`

### ❔ `.pth` file
untested
#### pros
- should fix the pip list issue not showing packages installed with `--target`
- also will fix other issues e.g. with `pip install upgrade`
#### cons
- adding a `.pth` file  in `program files/blender` might need admin privilege
- we have to manually reecreate the env, instead of not worry about it and rely on blender for this
- unsure if blender uses sitedir by default. 

### ✅ pass env vars 
we can't pass the env, but we can pass PYTHONPATH or PATH
this worked. see [PR](https://github.com/hannesdelbeke/blender_pip/pull/2/)

### manually parsing env vars
#### CON
- needs to be kept up to date. Blender is planning to change how user script paths work, so would need updating in future.

check what paths are, and if we can pass them as site dirs .

### Blender Python Paths
if we pass the existing current env, we shouldn’t have to parse the following vars.
> [!Blender script paths]-
> blender dir layout [docs](https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html)
> ```
> use e.g. bpy.utils.resource_path('USER')
> Search order: LOCAL, USER, SYSTEM. 
> ./scripts
> ./scripts/addons
> ./scripts/addons/modules
> ./scripts/addons_contrib
> ./scripts/addons_contrib/modules
> ./scripts/modules
> ./scripts/startup
> ./scripts/presets/{preset}
> ./scripts/templates_py
> 
> Search order: LOCAL, SYSTEM
> ./python
> ```
> 
> env vars [docs](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html#command-line-args-environment-variables)
> ```
> BLENDER_USER_RESOURCES
> BLENDER_USER_SCRIPTS
> BLENDER_SYSTEM_SCRIPTS
> BLENDER_SYSTEM_PYTHON
> ```
> 
> script folder set in settings