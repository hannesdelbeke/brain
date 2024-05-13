
[[Autodesk Maya]] represents your scene in 2 ways:
- **The dependency graph**
- [[Maya scene hierarchy]]

The dependency graph is a chain of nodes, a series of instructions, describing how to get the current scene starting from scratch: 
1. create a sphere A
2. move these CVs
3. create a curve B

To edit the dependency graph, you can use the [[Maya node editor]]

The connections between creation and editing nodes is also called [construction history](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-503E227B-EF49-4A78-B3CA-7EAC588017C9), because it records the history of how the scene was constructed

- official [docs](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-51096BC4-32B7-4391-BE39-21641B374745)