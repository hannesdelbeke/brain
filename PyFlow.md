https://github.com/wonderworks-software/PyFlow
Apache-2.0 license

a [[node editor]] for [[Python]] and [[Qt]] using [[QtPy]]

> [!WARNING] There are multiple pyflow projects
> Don't confuse PyFlow with the [pyflow](https://pyflow-workflow-generator.readthedocs.io/en/latest/content/introduction.html) on read-the-docs that wraps `ecflow`, 
> or the [pyflow](https://pypi.org/project/pyflow/)  Python package on pip for dependency management


![](https://raw.githubusercontent.com/wonderworks-software/PyFlow/master/PyFlow/UI/resources/PyFlow.png)
## Install

AFAIK Pyflow is not on pip, use
`pip install git+https://github.com/wonderworks-software/PyFlow.git@master`

```python
import sys
import os

 # force use of pyside6 in pyqt, run before importing qtpy & pyflow
 # this prevents an error if pyside2 is installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["QT_API"] = "pyside6" 

from qtpy.QtWidgets import QApplication
from PyFlow.App import PyFlow  # a QMainWindow

app = QApplication([])
#w = PyFlow()
w = PyFlow.instance(software="standalone")
w.show()
app.exec()
```

main logic is described in [pyflow.py](https://github.com/wonderworks-software/PyFlow/blob/master/pyflow.py)

PRO
- uses [[QtPy]]
- can be evaluated without GUI

CON
- no good [docs](https://wonderworks-software.github.io/PyFlow/). missing get started page. had to read source code
- doesn't work in PySide2 anymore