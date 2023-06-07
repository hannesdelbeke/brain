---
sentiment:
- 5
sentiment-hash: 324515ee
sentiment-label:
- factual
tags:
- technical
---

```python
import maya.utils
from PySide2.QtWidgets import QApplication

def hello():
    print("hi")
    
app = QApplication.instance()
maya.utils.executeDeferred(app.aboutToQuit.connect, hello)
# app.aboutToQuit.connect(hello)
```

[[Maya Python]]
