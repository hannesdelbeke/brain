you can also enable tool tips in Maya's preferences
to set [[tooltip|tooltips]] visible in [[Autodesk Maya|Maya]] by code: 

TODO this needs updating to get action->menu->child actions... recursive

```python
#print(menu_bar.children())
for action in menu_bar.actions() :1
    #print(action)
    #print(action.menu())
    action.setToolTipsVisible(True)
```

shared to https://groups.google.com/g/python_inside_maya/c/IcMpXXmDnSM
and https://discourse.techart.online/t/is-there-a-way-to-get-tooltips-for-maya-menitem/15385/12

