![[print all qt resources-1676464679534.jpeg]]
tested in [[Autodesk Maya|Maya]]
Todo: swap to list to support rendering all icons
```python
from PySide2.QtCore import QDirIterator

it = QDirIterator(":", QDirIterator.Subdirectories)

all_resource_paths = []
while it.hasNext():
    value = it.next()
    if value.endswith(".png"):
        all_resource_paths.append(value)



import sys

from PySide2.QtWidgets import QApplication, QGridLayout, QPushButton, QStyle, QWidget
import PySide2.QtGui

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

       # icons = sorted([attr for attr in dir(QStyle) if attr.startswith("SP_")])
        layout = QGridLayout()

        for n, name in enumerate(all_resource_paths):
            btn = QPushButton()
            btn.setToolTip(name)
            pixmap = PySide2.QtGui.QPixmap(name)
            icon = PySide2.QtGui.QIcon(pixmap)
            btn.setIcon(icon)
            layout.addWidget(btn, n / 25, n % 25)

        self.setLayout(layout)

w = Window()
w.show()
```

[[Qt]]

#icons

#todo share this here https://discourse.techart.online/t/extracting-maya-icons/4094/6