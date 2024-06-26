---
aliases: 
- pip
- pip.exe
---
Used for [[package management]] in [[Python]], to install packages from [[Python Package Index]]
## references
[official docs](https://pip.pypa.io/en/stable/)
## todo
- [ ] #TODO instructions how to install
- [ ] article how to package
- [ ] article how to automatically package on GitHub w action
### gotchas
- usually ships with Python, but sometimes not. or sometimes pip is outdated
- If you modified the path dynamically, pip won't pick up on this unless you [[pass custom sys.paths to subprocess]]. So pip list might not show all installed packages.
- Don't assume pip is installed on a pc when distributing your scripts to others.
- pip install might install to a different location than you assume. 
> [!example]-
> e.g. if `pip.exe` and your packages live in a [[Autodesk Maya|Maya]] or [[Blender]] folder, you might assume pip install from within that app would install to the same site-packages folder. But instead it installs to `%appdata%/Python/...` 
> - [ ] #todo fix path example

local install
`python -m pip install -e path/to/SomeProject`

