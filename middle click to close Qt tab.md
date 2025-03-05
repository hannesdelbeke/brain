Mouse middle click closes tabs in Chrome & Obsidian
let's add this to Qt!

A good UX for [[navigation]], just like [[ctrl + W in Qt]] 
## Solution
You'll need to handle the `mousePressEvent` in a custom `QTabBar` to detect middle mouse button clicks and close the corresponding tab.

```python
from PySide6.QtWidgets import QTabBar, QTabWidget, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

class CustomTabBar(QTabBar):
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:  # Check for middle mouse button
            tab_index = self.tabAt(event.position().toPoint())  # Updated for PySide6
            if tab_index != -1:
                self.parent().removeTab(tab_index)  # Close the tab
        else:
            super().mousePressEvent(event)

class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(CustomTabBar())  # Set the custom tab bar

# Example usage
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    tab_widget = CustomTabWidget()
    tab_widget.addTab(QTabBar(), "Tab 1")
    tab_widget.addTab(QTabBar(), "Tab 2")
    tab_widget.addTab(QTabBar(), "Tab 3")
    tab_widget.show()

    sys.exit(app.exec())  # Updated for PySide6
```

### Explanation

1. **Custom** `QTabBar`**:**
    - A subclass of `QTabBar` is created to override the `mousePressEvent` method.
    - It checks if the middle mouse button (`Qt.MiddleButton`) was clicked.
    - If so, it identifies the tab at the cursor position using `self.tabAt(event.pos())` and removes it.
2. **Linking with** `QTabWidget`**:**
    - A `CustomTabBar` is set as the tab bar for the `QTabWidget`.
    - This ensures the middle-click logic is applied to the entire tab widget.
### Additional Considerations
- If you're working within Maya or another specific environment, ensure the focus remains on your tool's window. (tested in maya and works)
- Test for compatibility with other shortcuts and mouse interactions to avoid conflicts.

## tags
[[todo]]
[[Qt]]
[[Maya tool]]
[[tab]]

