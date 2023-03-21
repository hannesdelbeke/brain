Max and Maya don't expose their native qt widgets. But you can get them.

```python

from PySide2 import QtWidgets

main_window = None
for widget in QtWidgets.QApplication.topLevelWidgets():
	if type(widget) == QtWidgets.QMainWindow:
		main_window = widget
		break
#print(main_window.findChild(QtWidgets.QMenuBar))
menu_bar = main_window.findChild(QtWidgets.QMenuBar)
```

set tooltips visible in maya

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