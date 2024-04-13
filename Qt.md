QT is a UI framework with a python implementation.
this means it works in all apps that support Python.

This is great since it allows us to make UI and reuse it across apps.

pick one of the following py modules
- PySide2
- PySide6
- PyQt5 
- PyQt6

there are also modules to handle compatibility between the qt modules. 
- Qt.py
- qtpy

try not to mix and match multiple qt libs. not sure how it would handle a shared QApplication instance. or if you can run 2.

Several apps use QT for their UI
- 3ds [[Autodesk 3ds Max|max]]
- [[Autodesk Maya|Maya]]
- Krita

if QScroll area has layout issues with content, ensure it is `setWidgetResizable`
```python
scroll_area = QScrollArea(self)  
scroll_area.setWidgetResizable(True)
```
min size of child widgets also matters

modern themes
- https://github.com/Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6
- https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/PySide6

[[UI]]
[[Python UI]]
