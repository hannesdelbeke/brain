## wip
doesnt work yet


When you add a menu item to a default Maya menu (e.g. `Windows`, `Mesh`, `File`, ...) on startup, it overwrites the whole menu.
Run this before adding to the [[Maya menu]] to avoid overwriting the whole menu.
but this only supports strign commands. no callables.
```python
# As Maya builds its menus dynamically upon being accessed,
# we force its build here prior to adding our entry using it's
# native mel function call.
mel.eval("evalDeferred buildFileMenu")

# use maya.utils.executeDeferred for callables
# or use maya.cmds.evalDeferred for strings
maya.utils.executeDeferred(add_to_menu) 



```



```python


def add_to_filemenu():
    if hasattr(cmds, 'about') and not cmds.about(batch=True):
        # As Maya builds its menus dynamically upon being accessed,
        # we force its build here prior to adding our entry using it's
        # native mel function call.
        mel.eval("evalDeferred buildFileMenu")


        
        # Create a command string that will dynamically import and execute show()
        __file__ = os.path.abspath(inspect.getfile(show))
        modulename = os.path.splitext(os.path.basename(__file__))[0]

        def run_show_from_file(file_path, module_name):
            import importlib.util

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.show()

        show_command_str = (

            f"import importlib.util; "
            f"path = {repr(__file__)}; "
            f"spec = importlib.util.spec_from_file_location('{modulename}', path); "
            f"mod = importlib.util.module_from_spec(spec); "
            f"spec.loader.exec_module(mod); "
            f"mod.show()"
        )

        # Serialise function into string
        script = inspect.getsource(_add_to_filemenu)
        script += "\n_add_to_filemenu()"


        # If cmds doesn't have any members, we're most likely in an
        # uninitialized batch-mode. It it does exists, ensure we
        # really aren't in batch mode.
        cmds.evalDeferred(script)


def _add_to_filemenu():
    """Helper function that's serialised into a string and passed to evalDeferred.
    """
    from maya import cmds
    

    # icon = os.path.dirname(pyblish.__file__)
    # icon = os.path.join(icon, "icons", "logo-32x32.svg")

    cmds.menuItem("pyblishScene",
                  label="Maya Module Manager",
                  parent="mainWindowMenu",
                #   image=icon,
                  command="print('hi')")

```