to get the version in Maya, don't use 
```python  
import maya.cmds as cmds  
version = cmds.about(version=True)
```
this returns the Maya version (as a string), e.g. `u'2026'`.
But it doesn't work when you run Maya Preview Release, then it returns `u'Preview Release'`

instead use
```python
import maya.mel as mel
mel.eval('getApplicationVersionAsFloat')
```
which always returns the correct version (as a float), e.g. `2026`

[[Maya Python]]