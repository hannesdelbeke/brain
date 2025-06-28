When you add a menu item to a default Maya menu (e.g. `Windows`, `Mesh`, `File`, ...) on startup, it overwrites the whole menu.

There's a partial fix that works for some menus.
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


depending which menu, run a different build command

| menu name | command name                                                                                                                                      |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| File      | `buildFileMenu`                                                                                                                                   |
| Windows   | ?? there seems to be in `ViewMenu` but not working<br>There's no `buildWindowsMenu`<br>tried`mel.eval('evalDeferred "source ViewMenu;"')` no luck |
| Display   | ?? test buildDisplayMenu                                                                                                                          |
|           | ?? buildHelpMenu                                                                                                                                  |


[[Pyblish Maya]] handles this
adding itself to the `File` menu, but the same doesn't work for the window

[[RnD to add to maya windows menu on startup]]

