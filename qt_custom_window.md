This note discusses some kind of template for a frameless window in Qt.
likely centered around a frameless [[window]]


## Brainstorm
naming
frimple? simple frameless
frimple-py

can't find old notes

[chinese blog](https://www.cnblogs.com/zhiyiYo/p/14659981.html) with great explanation regarding qt frameless windows.
including shadows etc, requires **pywin32** and has some bugs.
see [repo](https://github.com/zhiyiYo/PyQt-Frameless-Window) ⭐150

goal
- simple FramelessWindow
	- all qt-s
	- pure python
	- no dependencies
- simple title bar
	- easy to customize 
	- presets for default behavior. 
		- minimize, maximize, close
		- exit, help button, app icon
		- unreal darkbar
		- blender darkbar
	- no dependencies
	- pure python
	- all qt-s
any extras should be optional dependencies.
let dev choose if they want them.
[[keep it simple]] to avoid advanced features such as aero breaking in e.g. [[Unreal]] or [[Blender]].

- [x] frameless window should be moved to sep history
- [x] sep module for title bar


no default dark theme support for qt titlebar
see this C++ [registry hack](https://github.com/envyen/qt-winDark/blob/main/winDark.cpp) to set windows dark hints, worth porting to Python?

[[tool idea]]
