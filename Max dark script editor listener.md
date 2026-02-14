
https://github.com/hannesdelbeke/dark-listener-max

## Issue
By default, [[Autodesk 3ds Max|3ds Max]] has a very bright script editor and Listener.

## R&D notes

Tried existing solutions:

> [!bug]- darkscintilla - doesn't work
> a popular dark theme for the MaxScript editor, but it seems to be unavailable now. It was based on the Scintilla editor used in MaxScript, and provided a dark color scheme for better readability in low-light environments.
> - Someone made this, but the download link appears dead (it works in Edge):
> - https://www.scriptspot.com/3ds-max/scripts/darkscintilla-maxscript-editor-dark-scheme
> - https://discourse.techart.online/t/darkscintilla-dark-scheme-for-maxscript-editor/1807
> - Some properties files can be [found on GitHub](https://github.com/MerlinEl/Micra/blob/37e40f9d061d53ad81333134f4a75096b4395600/Micra4/App/Maxscript_Settings/dark/MXS_EditorUser.properties). It is unclear how to install them.
> - The `.mzp` installer does not work: it installs in the correct folder, but nothing happens after restart.

> [!success]- Found dark Script Editor
> - This [thread](https://forums.cgsociety.org/t/change-background-color-in-maxscript-editor/1223336) explains how to set the Script Editor to a dark background.
>   Saving in the main Max install folder (`Ctrl+S`) and restarting does the trick ([[as admin|needs admin rights]]).

> [!success]- Found dark Listener
> You can set some colors with MAXScript System Globals. See the [documentation](https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=GUID-D5E7028F-51A9-4B64-B71E-C8C694136089).
> 
> Run this MAXScript to get a dark Listener background:
> ```maxscript
> inputTextColor=(color 200 200 200)
> listenerBackgroundColor=(color 50 50 50)
> outputTextColor=(color 105 152 54)
> macroRecorderBackgroundColor=(color 50 50 50)
> macroRecorderTextColor=(color 160 160 160)
> -- listenerSelectionBackgroundColor=0
> ```
> Source: [Autodesk thread](https://forums.autodesk.com/t5/3ds-max-ideas/listener-window-background-color/idi-p/7653908).

The existing solutions were tricky to install, or didn't run on startup, so I packaged them as a plugin: [github.com/hannesdelbeke/dark-listener-max](https://github.com/hannesdelbeke/dark-listener-max)

### Packaging Notes
Autodesk packaging example: https://help.autodesk.com/view/MAXDEV/2023/ENU/?guid=packagexml_example

**Useful paths**
Logs: 
`C:\Users\hanne\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\Network`
Startup scripts: 
`C:\Users\hanne\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\scripts\startup`
