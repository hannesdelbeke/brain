## Problem
Maya doesn't detect [[Python packages editable install|editable packages]] installed in `Documents\Maya\scripts`
because the site-packages in your documents folder are not a Python site dir.

## Solution
run this in maya to create usersetup to add site packages on startup.
this might clash with existing usersetups.

```python
import os
import site
import maya.cmds as cmds

def create_user_setup():
    """create a usersetup to add site packages from the documents folder"""
    # Get Maya version and construct the scripts folder path
    maya_version = cmds.about(version=True)
    
    if maya_version == "Preview Release":
        maya_version = 2026  # TODO update in future
        
    user_docs = os.path.expanduser("~\\Documents")
    scripts_folder = os.path.join(user_docs, f"maya\\{maya_version}\\scripts")
    
    # Ensure the scripts folder exists
    if not os.path.exists(scripts_folder):
        os.makedirs(scripts_folder)

    # Path to the userSetup.py file
    user_setup_path = os.path.join(scripts_folder, "userSetup.py")

    # Define the content to be written in userSetup.py
    content = (
        "import site\n"
        f"site.addsitedir(r\"{scripts_folder}\\site-packages\")\n"
        f"site.addsitedir(r\"{user_docs}\\maya\\scripts\\site-packages\")\n"
    )

    # Write the content to userSetup.py
    with open(user_setup_path, "w") as file:
        file.write(content)

    print(f"userSetup.py has been created at: {user_setup_path}")
    
create_user_setup()
```

## Research

We should install to site packages instead:
- C:\Users\H\Documents\maya\2026\scripts\site-packages
- C:\Users\H\Documents\maya\scripts\site-packages

These paths aren't by default included in maya site packages, similar too
[[Blender doesn't support editable Python packages]]
- this was highlighted in [[Maya site package manager]]
- there's commented out code in py-pip to handle this. but only on install, not startup.
-   TODO, create startup maya solution.

current workaround, run on startup.
```python
import site
site.addsitedir(r"C:\Users\H\Documents\maya\2026\scripts\site-packages")
site.addsitedir(r"C:\Users\H\Documents\maya\scripts\site-packages")
```

maya only includes 
```
site packages [
'D:/Program Files/Autodesk/Maya2026\\Python', 
'D:/Program Files/Autodesk/Maya2026\\Python\\Lib\\site-packages']

user site packages
C:\Users\H\AppData\Roaming\Python\Python311\site-packages
```

can we install a script in site packages to add the folders in documents?
```python
import site
site.addsitedir(r"C:\Users\H\Documents\maya\2026\scripts\site-packages")
site.addsitedir(r"C:\Users\H\Documents\maya\scripts\site-packages")
```

after this i can import my custom edit installs but path still prints the old paths.
Turns out that `site.getsitepackages()` and `site.getusersitepackages()` are not designed to show the paths dynamically added using `site.addsitedir()`

To see dynamic added paths use
```python
import sys
print("\n".join(sys.path))
```

default sys paths
`C:/Users/H/Documents/maya/2026/scripts/site-packages`Maya includes it in `sys.paths`
`C:/Users/H/Documents/maya/scripts/site-packages` isn't in paths

i edit installed plugget to 
- `C:/Users/H/Documents/maya/scripts`
- `C:/Users/H/Documents/maya/2026/scripts/site-packages`
they default show up in sys.paths, but they'r not a sitedir.
[[plugget]] is only importable after adding it with `sys.addsitedir`


