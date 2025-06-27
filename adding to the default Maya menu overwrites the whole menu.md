When you add a menu item to a default Maya menu (e.g. `Windows`, `Mesh`, `File`, ...) on startup, it overwrites the whole menu.
Run this before adding to the [[Maya menu]] to avoid overwriting the whole menu.
```python
# As Maya builds its menus dynamically upon being accessed,
# we force its build here prior to adding our entry using it's
# native mel function call.
mel.eval("evalDeferred buildFileMenu")

# use maya.utils.executeDeferred for callables
# or use maya.cmds.evalDeferred for strings
maya.utils.executeDeferred(add_to_menu) 



```
