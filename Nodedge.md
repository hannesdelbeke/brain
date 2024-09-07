https://github.com/nodedge/nodedge
MIT licence

a [[node editor]] for [[Python]], similar to [[PyFlow]]

CON
- is this still in dev? no issues from this year, not many stars, last commit 9month ago
  [[PyFlow]] seems more active
## PRO
- has a [getting started](https://nodedge.io/#/resources) docs page
- supports [[PySide6]] & Python 3
- tested in Blender

TODO
- [ ] look into making custom nodes and defining workflows
	seems workflows are saved as json

### install
```
pip install nodedge
```
### demo
code to launch the node editor (based on the calculator example)
```python
import sys
from PySide6.QtWidgets import QApplication
from nodedge.mdi_window import MdiWindow

app: QApplication = QApplication.instance() or QApplication(sys.argv)
window = MdiWindow()
window.show()
sys.exit(app.exec_())
```
