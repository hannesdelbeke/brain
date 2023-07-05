maya supports both [[Qt]] & build-in functions to make menus.
the build-in functions are simpler, [see](https://groups.google.com/g/python_inside_maya/c/IcMpXXmDnSM/m/5Z7tKEaCCwAJ) 

[[unimenu]] uses the build-in methods
code to list maya menus.
```python
def find_menu(name):
    gMainWindow = maya.mel.eval('$temp=$gMainWindow')
    # get all the menus that are children of the main menu
    mainWindowMenus = maya.cmds.window(gMainWindow, query=True, menuArray=True)
    for menu in mainWindowMenus:
        print(menu)
        if menu.lower() == name.lower():
            return menu
```

## interesting

> [!slack convo]
> **Bob White** 
> Depends on what and where.  
> But if specifically trying to query items in the default menus you usually need to execute their on-first-open command (can't remember the actual name for it)
> 
> **Bob White**
> But basically all menu's are empty at startup until you click around
> 
> **H** 
> once i have a menu or menu item it's easy to get the children.  
> but how can i get that first `menuitem`. use case is add a submenu to an existing menu in code
> 
> **Bob White**
> for some reason I thought you could use `postMenuCommand` to query the command and then run it. But it doesn't have the query flag in the documentation.
> 
> I don't have a copy of Maya in front of me, but you can probably dig the command out of one of the `mel` files in maya, and basically query the menu, if it doesn't have children yet, run the command, and then work with it. 
> 
> **Travis Evashkevich**!
> I wish `QMenu` had an easy way to get the children from it, as you can just get the `QMainWindow` of Maya, get `menuBar` and that gives you all the menus from the looks of it, but yeah finding the children is a pita..
> 
> **Bob White** 
> Children don't exist yet, at least not until you've opened them once.  
> Maya's startup would be all the slower if it didn't defer some of those
> 
> **Bob White**
> Plus plugins loading etc...
> 
> **Shea Richardson**
> If it is a `qmenu` there is .actions
> And if the action has a menu, it's `action.menu`
> Or something like that?
> Our menus are pure Qt
> So that is how we access menu items
> 
> **Travis Evashkevich**
> Ah that's interesting, I hadn't thought about .actions being the .children


****

- great [ref](https://github.com/morganloomis/ml_tools/blob/master/scripts/ml_toolbox.py) for maya menu code
more [code samples](https://www.programcreek.com/python/?CodeExample=get+main+window)

get all maya menu commands, [source](https://www.reddit.com/r/Maya/comments/tcp7uy/query_menuitem_command_via_pyside/)
```python
from maya import cmds, mel
menu_items_and_their_commands = {}
for menu in cmds.window(mel.eval('$temp1=$gMainWindow'), q=True, ma=True):
    menu_items_and_their_commands[menu] = {}
    for item in cmds.menu(menu, q=True, ia=True) or []:
        menu_items_and_their_commands[menu][item] = cmds.menuItem(item, q=True, c=True)
```