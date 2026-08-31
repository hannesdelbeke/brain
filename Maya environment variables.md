---
aliases:
- Maya print paths
sentiment:
- 5
sentiment-hash: 09b0b60e
sentiment-label:
- factual
tags:
- technical
- work
---

MAYA_PLUG_IN_PATH [[maya plugin path]]
MAYA_MODULE_PATH 
MAYA_SCRIPT_PATH 
XBMLANGPATH (icons)

MAYA_LOCATION - maya install path

For the system PATH variable, 
- Maya adds `$MAYA_LOCATION/bin`.
- On Linux, it also adds `/usr/autodesk/com/bin`.

for more env vars see 
- env var [docs](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-925EB3B5-1839-45ED-AA2E-3184E3A45AC7)
- env var [file path docs](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-228CCA33-4AFE-4380-8C3D-18D23F7EAC72)

e.g. print all maya plugin paths
```python
import os
[print(x) for x in os.environ.get('MAYA_PLUG_IN_PATH', []).split(";") if x]
```

[[environment variable]]
[[Maya Python]]
