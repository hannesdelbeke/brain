# WIP
[[Maya python]]
[[Qt]]

- [x] adds a widget under the file menu.
- [x] can we add it in the menu bar itself

```python
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
import math


def get_maya_main_window():
    """
    Get the main Maya window as a Qt widget
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window_widget = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    return main_window_widget
    
main_window = get_maya_main_window()

print(main_window)
menu_bar = main_window.findChild(QtWidgets.QMenuBar)

print(menu_bar)


from PySide2.QtWidgets import QApplication, QMainWindow, QMenu, QAction, QWidget, QLineEdit, QVBoxLayout, QWidgetAction


class CustomWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        layout.addWidget(self.search_bar)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        menu = self.menuBar()
        file_menu = menu.addMenu('File')

        # Create custom widget
        custom_widget = CustomWidget()

        # Create QWidgetAction and set custom widget
        widget_action = QMenu(self)
        widget_action.setDefaultWidget(custom_widget)

        # Add QWidgetAction to the menu
        file_menu.addAction(widget_action)

        self.setWindowTitle('Custom Widget in Menu')
        self.setGeometry(100, 100, 400, 300)

class TimeElapsedMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(TimeElapsedMenu, self).__init__(parent=parent)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.showTime)
        self.timer.start(1000)
        self.time = QtCore.QTime.currentTime()
        self.setTitle("0")
        
    def showTime(self):
        time = self.time.elapsed()
        seconds = int(math.floor(time/1000))
        minutes = int(math.floor(seconds/60))
        hours = int(math.floor(minutes/60))
        # Mod 60 only at time of printing, otherwise above maths will not work
        text = "{h}:{m}:{s}".format(h=hours,m=(minutes%60),s=(seconds%60))
        self.setTitle(text)

# ---
main_file_menu =  menu_bar.findChild(QtWidgets.QMenu)
print("obj", menu_bar.findChild(QtWidgets.QMenu).objectName())
custom_widget = CustomWidget()

# Create QWidgetAction and set custom widget
widget_action = QWidgetAction(main_window)
widget_action.setDefaultWidget(custom_widget)

# Add widget to the menubar
menu_bar.addMenu(TimeElapsedMenu())

# Add widget in submenu
main_file_menu.addAction(widget_action)

```