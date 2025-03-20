[[Autodesk Maya]] has a [[metadata]] API that allows storing scene-wide metadata independent of objects.

- supported types: string, int, and float
- [docs](https://help.autodesk.com/view/MAYAUL/2025/ENU/?guid=GUID-52A836EE-9A09-4B50-8C44-1A6941EAE9D7)


```python
import maya.api.OpenMaya as om

# Get the current scene
scene = om.MFileIO.getCurrentFile()

# Create metadata object
metadataStream = om.MFnDependencyNode().create("metadataNode")

# Set metadata value (e.g., project name)
cmds.setAttr(f"{metadataStream}.stringAttr", "Project XYZ", type="string")
```

you can use [[mayapy]] to access this metadata externally

