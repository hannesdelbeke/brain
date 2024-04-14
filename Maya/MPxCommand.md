`MPxCommand` is a base class for creating custom commands, that can be run from `maya.cmds`. 

[[quick launcher]] can read all the commands in a nice GUI.

Sample [[Autodesk Maya|Maya]] Python code for a custom `MPxCommand` command that creates a cube. 

```python
import maya.api.OpenMaya as om
import maya.cmds as cmds

class CreateCubeCommand(om.MPxCommand):
    commandName = "createCube"

    def __init__(self):
        super(CreateCubeCommand, self).__init__()

    def doIt(self, args):
        # Parse the arguments if needed (not used in this example)

        # Create a cube
        cube = cmds.polyCube()[0]

        # Set the result to the name of the created cube
        self.setResult(cube)

# Creator function
def createCubeCommand():
    return om.asMPxPtr(CreateCubeCommand())

# Initialize the plugin
def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.registerCommand(
            CreateCubeCommand.commandName,
            createCubeCommand
        )
    except:
        om.MGlobal.displayError(
            "Failed to register command: {}".format(
                CreateCubeCommand.commandName
            )
        )

# Uninitialize the plugin
def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.deregisterCommand(CreateCubeCommand.commandName)
    except:
        om.MGlobal.displayError(
            "Failed to unregister command: {}".format(
                CreateCubeCommand.commandName
            )
        )

# Usage:
# 1. Save this script as "createCubeCmd.py"
# 2. Load the script in Maya using the following commands:
#    ```
#    import maya.cmds as cmds
#    cmds.loadPlugin("path/to/createCubeCmd.py")
#    ```
# 3. Run the custom command:
#    ```
#    cmds.createCube()
#    ```
```

[[maya python]]