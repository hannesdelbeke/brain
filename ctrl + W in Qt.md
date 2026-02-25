---
views: 2
---
You can add a `QShortcut` for the ctrl-W [[close tab]] to your widget class to close the widget-window when the shortcut is pressed. This will work without interfering with Maya's global shortcuts as long as your tool has focus.
### Steps to Add `Ctrl+W` Shortcut

Modify the widget by adding:
```python
# Add Ctrl+W shortcut to close window
shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
shortcut.activated.connect(self.close)
```

example
```python
class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Add Ctrl+W shortcut to close window
        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self)
        shortcut.activated.connect(self.close)
```

### Will Capturing Keys Cause Issues in Maya/Blender?
No, as long as the shortcut is added to your widget instance, it will only be active when your tool's window has focus. Maya's other keybindings will remain unaffected.

## UX issues
this works for custom tools, but it doesn't work with Maya's native tabs.

[[shortcut]]
[[qt]]
