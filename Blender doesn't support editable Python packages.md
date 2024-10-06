By default, an editable install to the user's modules folder will fail to import in [[Blender]].
## Why this happens
1. an editable install installs a `.pth` in the modules folder.
2. The modules folder is not in the sitedir path, so `.pth` files are not processed.
3. The solution is to add the modules folder to the sitedir on Blender startup
   
## How to editable install a repo 
1. git clone to a folder, e.g. `c:/repos/myrepo`  
2. ensure it's packaged with a `.toml` or `setup.py`
3. choose one of the below methods to editable install your folder.

> [!blender pip addon (recommended)]-
> ### blender pip addon (recommended)
> 1. install [[Blender pip addon]] addon
> 2. in Blender PIP, enter `-e c:/repos/myrepo` and click install 
>    (don't use `"` for the path, not sure how to handle spaces in path)
> 3. done!
> 
> blender pip auto adds the startup script if not there yet.

> [!Manual]-
> ### manual (advanced)
> - 
   Place following script in the startup folder. Blender will auto import it on startup.
> ```python
> """
> Place in [[Blender]] startup folder, so user module paths are added to sitedir when Blender starts.
> This enables `.pth` processing, which is needed for editable installs.
> Without this, editable install to user module path won't work correctly.
> """
> import site
> import bpy
> 
> user_scripts_path = Path(bpy.utils.script_path_user())
> addon_modules_path = user_scripts_path / "addons/modules"
> modules_path = user_scripts_path / "modules"
> site.addsitedir(modules_path)
> site.addsitedir(addon_modules_path)
> ```
> - run `python -m pip install -e "path/to/file" --target "path/to/modules"`
> - You might get an error user and target are not compatible, in that case set user install explicitly to false. Default pip config in Blender sometimes has it enabled.
> - Also read [[pass custom sys.paths to subprocess]] when manually pip installing.

## references
- [[Python]]'s [site docs](https://docs.python.org/3/library/site.html) explain when `.pth` files are processed
- [[pass custom sys.paths to subprocess]] discovered that [[Blender]] doesn't use site packages much

These addons I wrote auto add the modules folder to the site packages path on startup: 
- [[Blender pip addon]]
- [[Blender pip Qt addon]]

[[Python packages editable install]]