---
sentiment:
- 5
sentiment-hash: 5e4d18e5
sentiment-label:
- factual
tags:
- technical
---

env vars see [docs](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-925EB3B5-1839-45ED-AA2E-3184E3A45AC7)
- MAYA_PLUG_IN_PATH [[maya plugin path]]
- MAYA_MODULE_PATH

e.g. print all maya plugin paths
```python
import os
[print(x) for x in os.environ.get('MAYA_PLUG_IN_PATH', []).split(";") if x]
```

[[Maya Python]]
