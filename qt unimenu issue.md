In [[unimenu]], I ran into an issue with pyside6 ( [[Qt]]), actions are moved from `QtWidgets` to `QtGui`, so pyside6 apps didn't work.
fixed this
https://www.pythonguis.com/faq/pyqt5-vs-pyqt6/

## issue not finding mainwindow
CryEngine doesn't use a qmainwindow
instead it uses a widget with name mainWindow.
solved by searching topLevelWidgets with obj name mainwindow

## issue mainwindow garbage collected
in [[Autodesk 3ds Max|max]], after swapping to qt.
`RuntimeError: Internal C++ object (PySide2.QtWidgets.QMenuBar) already deleted.`
note sometimes this worked. unclear why.
global store var didn't work.
after global store mainwindow this was fixed

## issue davinci resolve
toplevelwidgets is empty