Launch the resource browser to see default available icons in [[Autodesk Maya]]
```python
import maya.app.general.resourceBrowser as resourceBrowser
resBrowser = resourceBrowser.resourceBrowser()
path = resBrowser.run()
```
- Search uses `startswith`, not `contains`!


a maya icon can be used in [[Qt]]
```python
from PySide import QtGui
icon = QtGui.QIcon(":/cube.png")  # to use cube.png
```

other
- qt image browser https://github.com/leocov-dev/maya-qt-img-resource-browser
- [[print all qt resources|print all default native qt icons]]
- https://charactersetup.com/?p=335 Icon Browser , gist [mirror](https://gist.github.com/hannesdelbeke/5d1a9c9b1d70ffbced64893e8d2c0156)
