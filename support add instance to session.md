take this sample node
```python
from datafix.core.collector import Collector  
from pathlib import Path  
  
class PathsInFolder(Collector):  
    folder_path = None  # settings that control the behavior of the collector  
    def logic(self):  
        """get all paths in a folder"""  
        folder = Path(self.folder_path)  
        return [p for p in folder.iterdir()]  
```
if you want to reuse nodes with different settings. You can't just do  
```python
p1 = PathsInFolder
p2 = PathsInFolder  
p1.folder_path = "C:/path1"  
p2.folder_path = "C:/path2"  
```
  
Both `folder_path` variables are  set to `path2`, because `folder_path` is a class attribute, not an instance attribute.  
```python
print(p1.folder_path)  # C:/path2
print(p2.folder_path)  # C:/path2
```
## Workaround
instead you can use inheritance to make duplicates:   
```python
class PathsInFolder1(PathsInFolder):  
    folder_path = 1  # settings that control the behavior of the collector  
  
class PathsInFolder2(PathsInFolder):  
    folder_path = 2  # settings that control the behavior of the collector  
    
p0 = PathsInFolder()  
p1 = PathsInFolder1()  
p2 = PathsInFolder2()  
print(p0.folder_path)  # None
print(p1.folder_path)  # 1
print(p2.folder_path)  # 2
```
## Easier solution
To avoid this. I added support to Session node registration (the add method) for instanced plugins. So you can instance a plugin, and use instance attributes instead of class attributes.
```python
p1 = PathsInFolder()
p2 = PathsInFolder()
p1.folder_path = "C:/path1"  
p2.folder_path = "C:/path2"  
print(p1.folder_path)  # C:/path1
print(p2.folder_path)  # C:/path2
```

[[datafix]]
[[Python stubs]]