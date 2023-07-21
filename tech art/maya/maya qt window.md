to correctly parent your widget to [[Autodesk Maya|Maya]]
- keeping the widget in front when clicking on other [[Autodesk Maya|maya]] windows
- hide the widget from alt tab apps,
You only need to pass the window flag 
```python
self.setWindowFlags(QtCore.Qt.Tool)
```

OPTIONAL: `setWindowFlags` resets the parent, so you can manually set the parent
```python
import pymel.core as pm
mayaWindow = pm.ui.Window("MayaWindow").asQtObject()
self.setParent(mayaWindow)
```

## other
you might want to make your window dockable in [[Autodesk Maya|maya]]: [[Maya dockable widget]]

[source](https://forums.cgsociety.org/t/pyside2-parent-window-to-main-window/1923035/8)
[outdated stackoverflow](https://stackoverflow.com/questions/22331337/how-to-get-maya-main-window-pointer-using-pyside/75249025#75249025)

[[Qt]]

 #ui #widget