
## try running in blender

```python
import bpy
import pytest

def get_non_zero_transform(mesh_object):
    """Check if the mesh object has non-zero transform"""
    loc = mesh_object.location
    rot = mesh_object.rotation_euler
    scale = mesh_object.scale

    return any(loc) or any(rot) or any(scale != (1, 1, 1))

def get_non_manifold_edges(mesh_object):
    """Check for non-manifold edges"""
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    non_manifold_edges = len(mesh_object.data.edges) > 0 and len([e for e in mesh_object.data.edges if e.select])
    bpy.ops.object.mode_set(mode="OBJECT")
    return non_manifold_edges

def get_zero_length_edges(mesh_object):
    """Check for edges with no length"""
    for edge in mesh_object.data.edges:
        vert1 = mesh_object.data.vertices[edge.vertices[0]].co
        vert2 = mesh_object.data.vertices[edge.vertices[1]].co
        if (vert1 - vert2).length == 0:
            return True
    return False

def has_empty_uv_sets(mesh_object):
    """Check if the mesh has empty UV sets"""
    return len(mesh_object.data.uv_layers) == 0

# Test cases

@pytest.mark.parametrize("mesh_name", [obj.name for obj in bpy.data.objects if obj.type == 'MESH'])
def test_non_zero_transform(mesh_name):
    mesh_object = bpy.data.objects[mesh_name]
    assert not get_non_zero_transform(mesh_object), f"Mesh '{mesh_name}' has non-zero transform!"

@pytest.mark.parametrize("mesh_name", [obj.name for obj in bpy.data.objects if obj.type == 'MESH'])
def test_non_manifold_edges(mesh_name):
    mesh_object = bpy.data.objects[mesh_name]
    assert not get_non_manifold_edges(mesh_object), f"Mesh '{mesh_name}' has non-manifold edges!"

@pytest.mark.parametrize("mesh_name", [obj.name for obj in bpy.data.objects if obj.type == 'MESH'])
def test_zero_length_edges(mesh_name):
    mesh_object = bpy.data.objects[mesh_name]
    assert not get_zero_length_edges(mesh_object), f"Mesh '{mesh_name}' has zero-length edges!"

@pytest.mark.parametrize("mesh_name", [obj.name for obj in bpy.data.objects if obj.type == 'MESH'])
def test_empty_uv_sets(mesh_name):
    mesh_object = bpy.data.objects[mesh_name]
    assert not has_empty_uv_sets(mesh_object), f"Mesh '{mesh_name}' has empty UV sets!"

# Run all the tests
pytest.main()
```

tried to run pytest in blender. but it errors on a disabled addon `node wrangler`

```
____ ERROR collecting builds/stable/blender-4.0.2-windows-x64/4.0/scripts/addons/node_wrangler/utils/paths_test.py ____
ImportError while importing test module 'D:\Program Files\Blender_Launcher_v1.16.1_Windows_x64\builds\stable\blender-4.0.2-windows-x64\4.0\scripts\addons\node_wrangler\utils\paths_test.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
builds\stable\blender-4.0.2-windows-x64\4.0\python\lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
builds\stable\blender-4.0.2-windows-x64\4.0\scripts\addons\node_wrangler\utils\paths_test.py:17: in <module>
    from .paths import match_files_to_socket_names
E   ImportError: attempted relative import with no known parent package
```

> [!NOTE] addons are not packages
> [[unpythonic]]
> [[Blender addon|Blender addons]] are weird because they are not meant to be in the PYTHONPATH despite being Python files. 
> - so pytest thinks they are packages.
> - pytest relies on `__init__.py` which the addon folders don't use
## Ignore Specific Path
prep stuff to make path relative TODO fix this
atm it gets user modules folder instead of addon install folder
```python

import bpy
from pathlib import Path


user_scripts_path = Path(bpy.utils.script_path_user())
pth_paths = [user_scripts_path / "modules", user_scripts_path / "addons/modules"]
startup_path = user_scripts_path / "startup"

# ignore folders
#pytest.main([f"--ignore={pth_paths[0]} --ignore={pth_paths[1]}"])
```

ignore the folder to run pytest successfully.

> [!warning]
> because of spaces and backslashes we need to use a raw string for this to work

```python
pytest.main([r"--ignore=D:\Program Files\Blender_Launcher_v1.16.1_Windows_x64\builds\stable\blender-4.0.2-windows-x64\4.0\scripts\addons"])
```

now pytest runs, but picks up various 3rd party tests, e.g. from pip.
`D:\Program Files\Blender_Launcher_v1.16.1_Windows_x64\builds\stable\blender-4.0.2-windows-x64\4.0\python\lib\site-packages\pip\_vendor\colorama\tests\winterm_test.py`

## specify included folder
we can specify included folders, but this wont work for pytests defined in dynamic code like in our above example
```python
pytest.main([r"D:\Program Files\path to folder"])
```
## run current file
```python
pytest.main(["-v", __file__])
```
only works if current script is saved, not if run from blender console.


[[Pytest]] uses [[pluggy]]

[[Python stubs]]
[[Blender snippet]]