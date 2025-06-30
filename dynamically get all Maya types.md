
run this in maya to get a list of all node types  
```python
from maya import cmds
node_types = cmds.ls(nt=True)  # 'AISEnvFacade', 'AlembicNode', ...  
```
  
print each one on a new line
```python
from typing import NewType  
for name in node_types: print(f"{name} = NewType('{name}', str)")  
```
copy the printed code in your script, e.g. [[datafix Maya]]  
  
```python
AISEnvFacade = NewType('AISEnvFacade', str)  
AlembicNode = NewType('AlembicNode', str)  
...
```
## How to use these types  
  
```python
from datafix_maya.types import Mesh  
Mesh('pCube1')  # this will create a Mesh type object with the data 'pCube1'  
```
now we can check if the string is a mesh-name, or just a string

[[Maya Python]]