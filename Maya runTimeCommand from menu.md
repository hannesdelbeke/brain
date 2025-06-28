new in 2022
shows up in [[Maya search]]

[[Maya runTimeCommand]]

- good example [maya docs](https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=GUID-36CB5BF4-BB31-41E8-81AF-CD03BDD2E4A6)
For example, if you had a script `userSetup.py` that creates a menu containing special Foo rendering scripts, you would need to convert this:

```python
cmds.menuItem(p=renderingMenu, l='Submit to Foo', c='import foo_maya;foo_maya.submit_dialog()')
```
to this:
```python
# Create runTimeCommand
cmds.runTimeCommand('SubmitToFoo', 
					default=True, 
					label='Send to Foo', 
					annotation='Send your scene to Foo for cloud rendering.', 
					category='Menu items.Cloud.Render', 
					command='import foo_maya;foo_maya.submit_dialog()', 
					keywords='render', 
					tags='Render' )

# Create menu
cmds.menuItem(p=renderingMenu, rtc='SubmitToFoo')
```

- [command reference docs](https://help.autodesk.com/cloudhelp/2022/ENU/Maya-Tech-Docs/CommandsPython/runTimeCommand.html)
- supports tags & categories
- can enable a plugin it relies on
- can have an image (icon)
	- [ ] todo example

[[Maya Python]]
[[Maya menu]]
