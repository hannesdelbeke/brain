imagine a [[Unreal tool]] to browse for console commands.
customize a command, and save it. (similar to the [[buttonizer]])
it can be used as a [[tool launcher]], it can be used to run commonly used commands

commands
- menu commands
- console commands
- custom python commands

features
- [[favorite]] commands
- [[categorize]] commands, e.g. by team or feature
- a [[cache]] with the most recently run commands
- a [[search bar]] to search commands
- support distributing a (preset) list of commands to your team or colleague

## console commands
this python code prints all commands in the output log
```python
import unreal
unreal.log("start collecting commands")
unreal.SystemLibrary.execute_console_command(None, "DumpConsoleCommands")
unreal.log("finished collecting commands")
```

get the output log in your unreal

```
C:\Projects\PROJECT_NAME\Saved\Logs\PROJECT_NAME.log
```

log contains
```
...
[2024.10.02-11.24.00:539][531]LogPython: unreal.SystemLibrary.execute_console_command(None, "DumpConsoleCommands")
[2024.10.02-11.24.00:539][531]Cmd: DumpConsoleCommands
[2024.10.02-11.24.00:539][531]DumpConsoleCommands: *
[2024.10.02-11.24.00:539][531]
[2024.10.02-11.24.00:539][531]Cmd: *
[2024.10.02-11.24.00:544][531]a.AccumulateLocalSpaceAdditivePose.ISPC
[2024.10.02-11.24.00:544][531]a.AnimNode.AimOffsetLookAt.Debug
[2024.10.02-11.24.00:544][531]a.AnimNode.AimOffsetLookAt.Enable
[2024.10.02-11.24.00:545][531]a.AnimNode.ControlRig.Debug
...
[2024.10.02-11.27.31:383][390]xr.VRS.FoveationPreview
[2024.10.02-11.27.31:383][390]xr.VRS.GazeTrackedFoveation
```

read whole log. start from the bottom. find `commands END`
then read all commands up until you find `Cmd: *`

i think some of these commands can contain input arguments
so maybe we save them as a customizable string.



