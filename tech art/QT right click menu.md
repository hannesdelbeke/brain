
overwrite your widget's method  `contextMenuEvent` 

make a menu in init of the main widget
```python
self.menu = QtWidgets.QMenu()  # used in contextMenuEvent
```
add this to a childwidget
```python
# create context menu when right c lick  
def contextMenuEvent(self, event):  
    widget = self.childAt(event.pos())
    menu = widget.parentWidget().menu  
    action = menu.exec_(self.mapToGlobal(event.pos()))
```
if only using 1 widget just forgo the parent code

use addaction to add menu entries
```python
self.menu.addAction("Action 1")
```

[[Qt]] 

#python