https://github.com/pyblish/pyblish-qml


related to [[Pyblish issues]]
## QML issues
#### Runs from a different interpreter than e.g. maya interpreter.
this can result in bugs. e.g. 
- import works in 1 python env, but not the other.
- different python versions
#### Crash in Py3
developed in Py2, not yet adapted to py3 [bug](https://github.com/pyblish/pyblish-qml/issues/372)
## QML is slow
QML is very slow compared to headless mode
since it added a fake wait, which can't easily be disabled
[issue](https://github.com/pyblish/pyblish-qml/issues/371)
