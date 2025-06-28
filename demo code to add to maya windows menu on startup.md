
this runs on [[Maya run on startup]]
[[Maya Python|Maya Python snippet]]

it can use some cleanup, tired now

```python
def add_to_filemenu():
    if hasattr(cmds, 'about') and not cmds.about(batch=True):
        # As Maya builds its menus dynamically upon being accessed,
        # we force its build here prior to adding our entry using it's
        # native mel function call.

        # mel.eval('evalDeferred "source buildDeferredMenus();"')
        mel.eval('evalDeferred buildDeferredMenus')


        # Create a command string that will dynamically import and execute show()
        __file__ = os.path.abspath(inspect.getfile(show))
        modulename = os.path.splitext(os.path.basename(__file__))[0]

        # Serialise function into string
        script = inspect.getsource(_add_to_filemenu)
        script += "\n_add_to_filemenu()"


        # mel.eval('global proc myWindowMenuBuilder() { python( "' + script + '" ); }')
        # mel.eval('addMenuItemSafe "mainWindowenu" "myWindowMenuBuilder" "moduleManagerMenuCallback";')

        # If cmds doesn't have any members, we're most likely in an
        # uninitialized batch-mode. It it does exists, ensure we
        # really aren't in batch mode.
        cmds.evalDeferred(script)


def _add_to_filemenu():
    """Helper function that's serialised into a string and passed to evalDeferred.
    """
    from maya import cmds
    # import inspect

    command = f"""
from maya import cmds
import importlib.util

module_name = "maya_module_manager"  # Replace with the actual plugin name
if cmds.pluginInfo(module_name, query=True, loaded=True):
    plugin_path = cmds.pluginInfo(module_name, query=True, path=True)

    spec = importlib.util.spec_from_file_location(module_name, plugin_path)
    maya_module_manager_py_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(maya_module_manager_py_module)
    maya_module_manager_py_module.show()
else:
    print("maya_module_manager plugin not found")"""

    cmds.menuItem("mayaModuleManagerMenu",
                  label="Maya Module Manager",
                  parent="mainWindowMenu",
                  command=command)
```

based on the solution in [[Pyblish Maya]]