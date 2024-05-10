`MPxCommand` is a base class for creating custom [[command|commands]], that can be run from `maya.cmds`

> [!warning] see runtime commands
> [[Maya runTimeCommand from menu]]

[[Maya quick launcher]] can read all the commands in a nice GUI.

Sample [[Maya Python|Maya Python]] code for a custom `MPxCommand` command that creates a cube. 

```python
import maya.api.OpenMaya as om
import maya.cmds as cmds

def maya_useNewAPI():
    """Tell Maya this plugin uses the Python API 2.0."""
    pass

def initializePlugin(plugin):
    vendor = "Dev"
    version = "1.0.0"
    om.MFnPlugin(plugin, vendor, version)

def uninitializePlugin(plugin):
    pass

class HelloWorldCmd(om.MPxCommand):
    COMMAND_NAME = "HelloWorld"

    def __init__(self):
        super(HelloWorldCmd, self).__init__()

    def doIt(self, args):
        """Called when the command is executed in script"""
        print("My First MPxCommand, Hello World!")

    @classmethod
    def creator(cls):
        """Returns an instance of the HelloWorldCmd"""
        return HelloWorldCmd()

def initializePlugin(plugin):
    """Entry point for a plugin"""
    vendor = "Dev"
    version = "1.0.0"
    plugin_fn = om.MFnPlugin(plugin, vendor, version)
    try:
        plugin_fn.registerCommand(HelloWorldCmd.COMMAND_NAME, HelloWorldCmd.creator)
    except:
        om.MGlobal.displayError("Failed to register command: {0}".format(HelloWorldCmd))

def uninitializePlugin(plugin):
    """Exit point for a plugin"""
    plugin_fn = om.MFnPlugin(plugin)
    try:
        plugin_fn.deregisterCommand(HelloWorldCmd.COMMAND_NAME)
    except:
        om.MGlobal.displayError("Failed to deregister command: {0}".format(HelloWorldCmd))
```

