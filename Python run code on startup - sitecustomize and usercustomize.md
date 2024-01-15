
sitecustomize.py and - usercustomize.py

a [[pythonic]] way to run code on startup, just place them in [[site-packages]].

any `sitecustomize.py` at the root of your repository will be evaluated before any application code runs


> [!warning] Title
> many apps don't support this. blender, maya .... todo list and confirm

test file `sitecustomize.py`
```python
print("TEST")

# write a text file to my doc
import os
from pathlib import Path
def write_test_file():
    """Write a test file to the user's Documents directory."""
    doc_path = Path.home() / "Documents" / "MyPluginTest.txt"
    with open(doc_path, "w") as f:
        f.write("This is a test file created by MyPlugin.")
    print(f"Test file written to: {doc_path}")


write_test_file()
```
- works in unreal in `C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\ThirdParty\Python3\Win64\Lib\site-packages`
- doesn't work in `plugin/content/python`
- doesn't work in `plugin/content/python/site-packages`


