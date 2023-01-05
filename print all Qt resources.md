---
alias: print all default native qt icons
---

![[print all qt resources-1676464679534.jpeg]]
tested in [[Autodesk Maya|Maya]] & pycharm

(a lot of overlap with https://github.com/hannesdelbeke/texture-browser-unreal-plugin)

Todo: swap to list to support rendering all icons
```python
from PySide2.QtCore import QDirIterator, Qt
from PySide2.QtWidgets import QApplication, QGridLayout, QLineEdit, QPushButton, QScrollArea, QWidget
import PySide2.QtGui

it = QDirIterator(":", QDirIterator.Subdirectories)

all_resource_paths = []
while it.hasNext():
    value = it.next()
    if value.endswith(".png"):
        all_resource_paths.append(value)

app = QApplication.instance() or QApplication()

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.layout = QGridLayout()

        for n, name in enumerate(all_resource_paths):
            btn = QPushButton()
            btn.setToolTip(name)
            pixmap = PySide2.QtGui.QPixmap(name)
            icon = PySide2.QtGui.QIcon(pixmap)
            btn.setIcon(icon)
            self.layout.addWidget(btn, n / 25, n % 25)

        self.create_search_bar()

        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        inner_widget = QWidget()
        inner_widget.setLayout(self.layout)

        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(inner_widget)

        main_layout = QGridLayout(self)
        main_layout.addWidget(self.search_bar, 0, 0)
        main_layout.addWidget(scroll_area, 1, 0)

    def create_search_bar(self):
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_buttons)

    def filter_buttons(self, text):
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item.widget():
                item.widget().setVisible(text.lower() in item.widget().toolTip().lower())

w = Window()
w.show()

app.exec_()
```

this displays the resource path when you hover over the icon.
however you can also access these paths through `QStyle` 

code for a folder 📁 icon
```python  
from PySide6.QtGui import QStyle
my_button.setIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon))
        
```
[[Qt]]
[[icon]]

#todo share this here https://discourse.techart.online/t/extracting-maya-icons/4094/6