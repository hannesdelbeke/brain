find the active [[Perforce]] workspace (=client) in [[Python]] with [[python-perforce]]
```python
import perforce
from pathlib import Path
 
p4 = perforce.connect()
demo_file = "C:\myproject\name.lastname-myproject-dev\Assets\test.ma"
 
def find_workspace_from_filepath(filepath: Path) -> str:
    """
    returns the name of (the first) workspace a file is in. e.g. name.lastname-myproject-dev'
    since p4 connect often doesn't have a client set, we can use this to set the client to connect to p4.

    use like this:
    p4 = perforce.connect()
    p4.client = find_workspace_from_filepath(filepath)
    """
    p4 = perforce.connect()
    info = p4.run(['clients', '--me'])  # find active workspaces
    # info can return multiple workspaces, filter the workspace with our file 
    for data in info:  # data is a dict
        root = data["Root"]  # get the rootpath of our workspace
        if filepath.is_relative_to(root):
            return data["client"]
 
workspace = find_workspace_from_filepath(demo_file)  # name.lastname-myproject-dev'

# i'm a bit unclear on when to use client, and when to use workspace.
p4.client = workspace  # assign the active workspace since it defaults to None
client = perforce.Client(workspace)  # unsure what this is TODO figure out
 # creates or gets a new changelist
changelist = perforce.changelist("name of changelist", p4)
```

[[Python snippet]]