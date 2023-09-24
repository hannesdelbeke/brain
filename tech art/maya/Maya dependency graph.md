The dependency graph is one of two ways [[Autodesk Maya]] represents your scene (the other being the scene hierarchy). It’s a chain of nodes.

The dependency graph is like a series of instructions describing how to get the current scene starting from scratch: 
1. create a sphere A
2. move these CVs
3. create a curve B

The connections between creation and editing nodes is also called [construction history](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-503E227B-EF49-4A78-B3CA-7EAC588017C9), because it records the history of how the scene was constructed

- official [docs](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-51096BC4-32B7-4391-BE39-21641B374745)