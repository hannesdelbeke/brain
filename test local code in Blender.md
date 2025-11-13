To make your python module importable in Blender, it needs to be included in the python path. You can just place a script in your scripts folder, however any good tooldev will create their script in a separate repo. So how can you sync it and test it in Blender?

options
- manually add to env
- symlink into env
- editable install + custom script to load [[pth|.pth]] files 
- install local addon/extension
	- the most stable and reliable way, only works if you packaged an addon
- TODO VS Code plugin - I don't have much experience with this. 
- blender env vars?

I often end up using symlink since it's the least effort, and I know what issues I can expect caused by git.

## Append path
to test a python package
1. add to path
```python
import sys
sys.path.append('/path/to/directory')
```
2. import and test

notes
- disappears between Blender sessions

## Symlink
Create a symbolic link to your blender scripts folder. ([[mklink windows - soft & hard link|Instructions for Windows]])

notes
- least effort, just run 1 line of code in the terminal once
- stays in your environment between Blender sessions
- works with any python module
- creates issues with [[git]], if git tries to delete the link e.g. when changing branch

## Editable install
[[Python packages editable install|editable install]] is the [[Pythonic]] way to symlink.
- doesn't work by default with Blender. It requires the [[Blender pip addon]] to load [[pth|.pth]] files.
- requires your module to be packaged so you can editable install it

## install local addon
to test an addon
1. set up your project as a blender addon
2. install a local [[Blender addon|addon]], browse to the folder, and click install

## reload code
[[python reload]] tends to miss things, better to either
- restart Blender
- or delete imported module var from memory, e.g. with [[qt-module-manager]]

[[Blender scripting]]
[[dev environment]]
[[TODO create local test env]]

[[Python env management]]