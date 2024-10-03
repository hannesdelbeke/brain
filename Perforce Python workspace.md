find the active [[Perforce]] workspace (=client) in [[Python]] with [[python-perforce]]
```python
import perforce
from pathlib import Path
 
p4 = perforce.connect()
demo_file = "C:\myproject\name.lastname-myproject-dev\Assets\test.ma"
 
def find_workspace_from_filepath(filepath):
    info = p4.run(['clients', '--me'])  # find active workspaces
    # info can return multiple workspaces, filter the workspace with our file 
    for data in info:  # data is a dict
        root = data["Root"]  # get the rootpath of our workspace
        if Path(demo_file).is_relative_to(root):
            return data["client"]
 
workspace = find_workspace_from_filepath(demo_file)  # name.lastname-myproject-dev'

# i'm a bit unclear on when to use client, and when to use workspace.
p4.client = workspace  # assign the active workspace since it defaults to None
client = perforce.Client(workspace)  # unsure what this is TODO figure out
 # creates or gets a new changelist
changelist = perforce.changelist("name of changelist", p4)
```
