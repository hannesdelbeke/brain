
```c#
global proc rebuildMenusList()
{
	global string $gMainWindow;
	// These are the main common menus which are shown only in the common menuSet
	string $commonMenus[] = {
		// These are menus that appear in menu bar by default
		"mainFileMenu",
		"mainEditMenu",
		"mainModifyMenu",
		"mainCreateMenu",
		"mainDisplayMenu",
		"mainWindowMenu"
	};
	// This is a list of menus that will not appear in All Menus list
	string $filterMenus[] = {
		// These are menus that appear in menu bar by default
		"mainFileMenu",
		"mainEditMenu",
		"mainModifyMenu",
		"mainCreateMenu",
		"mainDisplayMenu",
		"mainWindowMenu",
		// These help/test/bonustools menus are always shown at the end
		"HelpMenu",
		"MainHelpMenu",
		"bonusToolsMenu",
		"repoTestMenu", 
		// These are Hotbox menus
		"HotboxNorth1", "HotboxNorth2", "HotboxNorth3", 
		"HotboxSouth1", "HotboxSouth2", "HotboxSouth3", 
		"HotboxEast1", "HotboxEast2", "HotboxEast3", 
		"HotboxWest1", "HotboxWest2", "HotboxWest3", 
		"HotboxCenter1", "HotboxCenter2", "HotboxCenter3",
		"HotBoxRecentCommandsMenu", 
		"HotBoxControlsMenu"
	};
	...
```

this is all build in `global proc buildDeferredMenus` in `initMainMenuBar.mel`
however running this just crashes Maya with error:
`Object 'mainFileMenu' not found.` and `Object 'mainWindowMenu' not found.`
```c#
// Description:
//   This proc is provided so that users can choose to immediately build the main menus 
//	 that we now defer building for desktop heap memory reasons (as of Maya2009)
//	 (see bug 305296). It is not called by Maya on startup.  
//
global proc buildDeferredMenus()
{
	// File Menu
	buildFileMenu();

	// Edit Menu
	global string $gMainEditMenu;
	string $editMenu = "MayaWindow|" + $gMainEditMenu;

	buildEditMenu( $editMenu );

	// Window Menu
	global string $gMainWindowMenu;

	buildViewMenu ( $gMainWindowMenu );

	// Help Menu
	buildHelpMenu();
}
```

custom version
```

		global string $gMainFileMenu	= "mainFileMenu";
		global string $gMainEditMenu	= "mainEditMenu";
		global string $gMainModifyMenu	= "mainModifyMenu";
		global string $gMainDisplayMenu	= "mainDisplayMenu";
		global string $gMainWindowMenu	= "mainWindowMenu";
		global string $gMainCreateMenu	= "mainCreateMenu";
		global string $gMainSelectMenu	= "mainSelectMenu";
```
```c#
global proc buildDeferredMenus()
{
	// File Menu
	buildFileMenu();

	// Edit Menu
	global string $gMainEditMenu;
	string $editMenu = "MayaWindow|" + $gMainEditMenu;

	buildEditMenu( $editMenu );

	// Window Menu
	buildViewMenu ( "mainWindowMenu" );

	// Help Menu
	buildHelpMenu();
}
```
```


```python
mel.eval("evalDeferred buildFileMenu")
```

`mel.eval('evalDeferred "source ViewMenu;"')` 
leads to `Object 'mainFileMenu' not found.`
`

use `whatIs buildFileMenu` prints 
`C:/Program Files/Autodesk/Maya2024/scripts/startup/FileMenu.mel`

maybe we can use this
```
menu -e -postMenuCommand checkMainFileMenu $gMainFileMenu;
```



---


```python


def add_to_filemenu():
    if hasattr(cmds, 'about') and not cmds.about(batch=True):
        # As Maya builds its menus dynamically upon being accessed,
        # we force its build here prior to adding our entry using it's
        # native mel function call.
        mel.eval("evalDeferred buildFileMenu")


        
        # Create a command string that will dynamically import and execute show()
        __file__ = os.path.abspath(inspect.getfile(show))
        modulename = os.path.splitext(os.path.basename(__file__))[0]

        def run_show_from_file(file_path, module_name):
            import importlib.util

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.show()

        show_command_str = (

            f"import importlib.util; "
            f"path = {repr(__file__)}; "
            f"spec = importlib.util.spec_from_file_location('{modulename}', path); "
            f"mod = importlib.util.module_from_spec(spec); "
            f"spec.loader.exec_module(mod); "
            f"mod.show()"
        )

        # Serialise function into string
        script = inspect.getsource(_add_to_filemenu)
        script += "\n_add_to_filemenu()"


        # If cmds doesn't have any members, we're most likely in an
        # uninitialized batch-mode. It it does exists, ensure we
        # really aren't in batch mode.
        cmds.evalDeferred(script)


def _add_to_filemenu():
    """Helper function that's serialised into a string and passed to evalDeferred.
    """
    from maya import cmds
    

    # icon = os.path.dirname(pyblish.__file__)
    # icon = os.path.join(icon, "icons", "logo-32x32.svg")

    cmds.menuItem("pyblishScene",
                  label="Maya Module Manager",
                  parent="mainWindowMenu",
                #   image=icon,
                  command="print('hi')")

```