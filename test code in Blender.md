## Append path
to test a python package
1. add to path
```python
import sys
sys.path.append('/path/to/directory')
```
2. import and test

**notes**
- disappears on restart

## Symlink
or symbolic link [[mklink windows - soft & hard link]]

**notes**
- stays on restart
- can create issues with [[git]], if git tries to delete the link e.g. when changing branch

## install local addon
to test an addon
1. set up your project as a blender addon
2. install a local [[Blender addon|addon]], browse to the folder, and click install

## reload code
reload tends to miss things, better to either
- restart Blender
- or delete imported module var from memory

[[Blender scripting tips]]
[[dev environment]]
[[TODO create local test env]]

[[Python env management]]