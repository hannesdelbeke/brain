this code has a small issue with the eventtrap. 
it's deleted from memory before trying to access it sometimes.
feels a bit hacky but doesnt work without this

```python
from PySide6.QtWidgets import (  
    QWidget, QGridLayout, QVBoxLayout, QApplication,  
    QPushButton, QMainWindow, QGroupBox, QLabel)  
from PySide6.QtCore import Qt, QEvent, QMimeData  
from PySide6.QtGui import (QMouseEvent, QDrag, QMouseEvent, QDragEnterEvent,  
                         QDropEvent, QColor, QPalette, QFont)  
  
  
class MovableWidget(QGroupBox):  
    """Exteremely simple widget with a button and a label to move around"""  
  
    def __init__(self, r, c, parent=None):  
        super().__init__(parent=parent)  
        self.setFixedSize(400, 200)  # So we have some area to grab on to  
        # Store row/column for label        self.r = r  
        self.c = c  
  
        # Setup a button for a basic QObject element to use  
        self.btn = QPushButton(f"BUTTON: {r} {c}")  
        self.btn.clicked.connect(self.btnClick)  
        # Setup a Qlabel to show updated row/column  
        self.lbl = QLabel(f"Current Loc: {r} {c}")  
  
        # Set font larger  
        fnt = QFont()  
        fnt.setPointSize(15)  
        self.btn.setFont(fnt)  
        self.lbl.setFont(fnt)  
  
        # Basic layout to setup widget  
        tmpLayout = QVBoxLayout()  
        tmpLayout.addWidget(self.btn)  
        tmpLayout.addWidget(self.lbl)  
        self.setLayout(tmpLayout)  
  
        # Fill widget background with some color, so we can better see it.  
        self.setAutoFillBackground(True)  
        palette = self.palette()  
        palette.setColor(QPalette.ColorRole.Window, QColor("#C5E0B4"))  
        self.setPalette(palette)  
  
    def btnClick(self, btn):  
        """Display button text to console """  
        sender: QPushButton = self.sender()  
        textSender = sender.text()  
        print(f"Button Pressed: [{textSender}]")  
  
    def relabel(self, r, c):  
        """Set button label text given row/col"""  
        self.lbl.setText(f"Current Loc: {r} {c}")  
  
  
class MyAppMainWin(QMainWindow):  
    """ Basic Main Window, but with gridLayout configured to allow for movable objects """  
  
    def __init__(self, parent=None):  
        super().__init__()  
        self.target = None  
        self.setAcceptDrops(True)  
        self.gridLayout = QGridLayout()  
  
        for i in range(3):  
            for j in range(3):  
                myobj = MovableWidget(i, j)  # a widget to move around  
                myobj.installEventFilter(self)  
  
                self.gridLayout.addWidget(myobj, i, j)  
                self.gridLayout.setColumnStretch(i % 3, 1)  
                self.gridLayout.setRowStretch(j, 1)  
  
        # Assign base widget w/ given layout as main/central widget  
        self.baseMainWidget = QWidget()  
        self.baseMainWidget.setLayout(self.gridLayout)  
        self.setCentralWidget(self.baseMainWidget)  
  
        # I was experiencing a double 'mousePressEvent', every time that I  
        # clicked into a widget. The event trap holds the press event till        # release or dropEvent        self.eventTrap = None  
  
    def eventFilter(self, watched, event: QEvent):  
        if event.type() == QEvent.Type.MouseButtonPress:  
            self.mousePressEvent(event)  
        elif event.type() == QEvent.Type.MouseMove:  
            self.mouseMoveEvent(event)  
        elif event.type() == QEvent.Type.MouseButtonRelease:  
            self.mouseReleaseEvent(event)  
        return super().eventFilter(watched, event)  
  
    def get_index(self, pos) -> int:  
        """Helper Function = get widget index that we click into/drop into"""  
        for i in range(self.gridLayout.count()):  
            contains = self.gridLayout.itemAt(i).geometry().contains(pos)  
            if contains and i != self.target:  
                return i  
  
    def mousePressEvent(self, event: QMouseEvent):  
        if event.button() == Qt.MouseButton.LeftButton:  
            if self.eventTrap is None:  
                self.eventTrap = event  
                self.target = self.get_index(event.scenePosition().toPoint())  
            elif self.eventTrap == event:  
                pass  
            else:  
                print("Something broke")  
        else:  
            self.target = None  
  
    def mouseMoveEvent(self, event: QMouseEvent):  
        if event.buttons() & Qt.MouseButton.LeftButton and self.target is not None:  
            drag = QDrag(self.gridLayout.itemAt(self.target).widget())  
            pix = self.gridLayout.itemAt(self.target).widget().grab()  
            mimedata = QMimeData()  
            mimedata.setImageData(pix)  
            drag.setMimeData(mimedata)  
            drag.setPixmap(pix)  
            drag.setHotSpot(event.pos())  
            drag.exec()  
  
    def mouseReleaseEvent(self, event):  
        # Reset our event trap & target handles. Note 'mouseReleaseEvent' is not called  
        # if dropEvent happens, at least in my experience        self.target = None  
        self.eventTrap = None  
  
    def dragEnterEvent(self, event: QDragEnterEvent):  
        if event.mimeData().hasImage():  
            event.accept()  
        else:  
            event.ignore()  
  
    def dropEvent(self, event: QDropEvent):  
        """Check if swap needs to occur and perform swap if so. """  
        eventSource: QVBoxLayout = event.source()  # For typehinting the next line  
        if not eventSource.geometry().contains(event.position().toPoint()):  
            source = self.get_index(event.position().toPoint())  
            if source is None:  
                self.eventTrap = None  
                self.target = None  
                return  
            i, j = max(self.target, source), min(self.target, source)  
            p1, p2 = self.gridLayout.getItemPosition(i), self.gridLayout.getItemPosition(j)  
  
            # Update widget.lbl prior to moving items, while item handles are useful  
            self.gridLayout.itemAt(i).widget().relabel(p2[0], p2[1])  
            self.gridLayout.itemAt(j).widget().relabel(p1[0], p1[1])  
  
            # The magic - pop item out of grid, then add item at new row/col/rowspan/colspan  
            self.gridLayout.addItem(self.gridLayout.takeAt(i), *p2)  
            self.gridLayout.addItem(self.gridLayout.takeAt(j), *p1)  
            # Always reset our event trap & target handles.  
            self.target = None  
            self.eventTrap = None  
  
  
if __name__ == '__main__':  
    app = QApplication([])  
    w = MyAppMainWin()  
    w.show()  
    app.exec()
```

[[qt snippets]]