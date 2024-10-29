[[Autodesk 3ds Max]] and [[Autodesk Maya|Maya]] don't expose their native qt widgets. But you can get them.

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

see [[force tooltips in Maya]] to use tooltips