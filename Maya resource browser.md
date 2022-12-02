Launch the resource browser to see default available icons in Autodesk Maya
```python
import maya.app.general.resourceBrowser as resourceBrowser
resBrowser = resourceBrowser.resourceBrowser()
path = resBrowser.run()
```
- Maya resource browser's search uses `startswith`, not `contains`!
## Qt default Maya icons
a default maya icon can be used in [[Qt]], but custom ones can't without extra steps
```python
from PySide2 import QtGui, QtWidgets
icon = QtGui.QIcon(QtGui.QPixmap(':/cube.png'))  # to use cube.png
btn = QtWidgets.QButton
```
## Qt Custom Maya icons
find icons in registered maya icon paths.
they are not included in maya resources, so need to be searched manually in `XBMLANGPATH` paths
```python
def get_icon_path(name) -> Optional[str]:
    default_name = "cube.png"
    name = name or default_name
    for icon_dir in os.environ.get('XBMLANGPATH', '').split(os.pathsep):
        icon_path = os.path.join(icon_dir, name)
        if os.path.exists(icon_path):
            return icon_path
    if name != default_name:
        return get_icon_path(default_name)
```

other
- qt image browser https://github.com/leocov-dev/maya-qt-img-resource-browser
- [[print all Qt resources|print all default native qt icons]]
- https://charactersetup.com/?p=335 Icon Browser , gist [mirror](https://gist.github.com/hannesdelbeke/5d1a9c9b1d70ffbced64893e8d2c0156)

create a test widget in Maya to show an icon
```python
from PySide2 import QtWidgets, QtGui

class IconWidget(QtWidgets.QWidget):
    def __init__(self):
        super(IconWidget, self).__init__()
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel()
        icon = QtGui.QIcon(QtGui.QPixmap(':/cube.png'))
        label.setPixmap(icon.pixmap(64, 64))
        layout.addWidget(label)
        self.setLayout(layout)
w = IconWidget()
w.show()
```
[[Qt]]
[[icon]]
[[Maya python]]

relates to [[print all Qt resources]]