
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



got it to work 
[[demo code to add to maya windows menu on startup]]

but am interested in [[Maya runTimeCommand from menu]]
since `defaultRunTimeCommands.mel` in startup uses them:
```c#
runTimeCommand -default true
	-label 		(uiRes("m_defaultRunTimeCommands.kShelfEditorLbl")) 
	-annotation (uiRes("m_defaultRunTimeCommands.kShelfEditorAnnot"))
	-category   ("Menu items.Common.Windows.Settings/Preferences")
	-command    ("shelfEditorDialog")
	ShelfPreferencesWindow;
```