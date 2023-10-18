Simplify your Python [[package management]] with a [[Python pip|pip]] manager that can run in Maya, Max, Substance, Unreal, Blender, ...

repo: https://github.com/hannesdelbeke/pip-qt

![](https://user-images.githubusercontent.com/3758308/273054100-272b56de-ada0-45f3-a813-75db8a749688.png)

## Features
- [x] add uninstall
- [x] add sort column support

low priority 
- [ ] add reload (hacky)
- [ ] add button to open folder (in explorer) => would speed up dev. i often go to folder & delete it
- [ ] add pip dependencies UI
- [ ] update all button
- [ ] select a package, auto fill the name in search field. WHY? e.g. to quicker uninstall
- [ ] atm we show packages installed, not modules. it'd be great to have a module browser
UI for this https://github.com/tox-dev/pipdeptree
this is related https://github.com/ddelange/pipgrip

## Reference

related to [[Blender pip addon]] 
we can reuse [[plugget qt ui]] for pip

https://github.com/open-cogsci/python-qtpip 3y old, uses pip search, outdated, unclear docs
https://github.com/techbliss/Pip_QT_Gui 8 year old, PyQt4
https://github.com/NathanVaughn/PipQt 4year old, - PySide2, nice UI
![](https://github.com/NathanVaughn/PipQt/raw/master/screenshots/main.jpg)


