|Maya uses [[PySide]] ([[Qt]]). The main window is `<PySide2.QtWidgets.QMainWindow(0x2a185b32800, name="MayaWindow")`

print top widgets with no parent
```python
from PySide2 import QtWidgets
for widget in QtWidgets.QApplication.topLevelWidgets():
    if widget.parent():
        continue
    print(widget)
```

widgets need to be parented to the main window 
- so they don't lose focus and disappear behind |maya when using maya. 
- and aren’t garbage collected.

[[Maya Python]]