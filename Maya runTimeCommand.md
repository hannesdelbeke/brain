If you create a `runTimeCommand` at startup, set `default` to `true`. So it won't save the command.

```python
import maya.cmds as cmds

cmds.runTimeCommand(
		'myUniqueName',
		label="hello",
		annotation='This is my command',
		category='Menu items.Common.Windows.Settings/Preferences',
		command='print("Hello World")',
		default=True
)

cmds.menuItem(p="mainFileMenu", rtc='myUniqueName')
```

TODO figure out how category works


https://help.autodesk.com/cloudhelp/2022/ENU/Maya-Tech-Docs/CommandsPython/runTimeCommand.html


