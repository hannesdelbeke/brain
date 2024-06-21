By default, [[Autodesk 3ds Max|3ds Max]] has a very bright script editor and listener.

## MAXScript System Globals
You can set some colors with system globals, see [docs](https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=GUID-D5E7028F-51A9-4B64-B71E-C8C694136089)
run this maxscript to get a dark background in the listener:
```maxscript
inputTextColor=(color 200 200 200)
listenerBackgroundColor=(color 50 50 50)
outputTextColor=(color 105 152 54)
macroRecorderBackgroundColor=(color 50 50 50)
macroRecorderTextColor=(color 160 160 160)
-- listenerSelectionBackgroundColor=0
```
source: [thread](https://forums.autodesk.com/t5/3ds-max-ideas/listener-window-background-color/idi-p/7653908)

## manually set theme
[thread](https://forums.cgsociety.org/t/change-background-color-in-maxscript-editor/1223336) instructing how to set the script editor to a dark background 
Saving this in main max install folder (ctrl-s) ([[as admin|needs admin rights]]) , and restart, does the trick.
- [x] packaged see [repo](https://github.com/hannesdelbeke/dark-listener-max)

tested max packaging
https://help.autodesk.com/view/MAXDEV/2023/ENU/?guid=packagexml_example
c:/max test plug
- logs `C:\Users\hanne\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\Network`
- `C:\Users\hanne\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\scripts\startup`

## darkscintilla
someone made this, but download link is dead (works in edge)
- https://www.scriptspot.com/3ds-max/scripts/darkscintilla-maxscript-editor-dark-scheme
- https://discourse.techart.online/t/darkscintilla-dark-scheme-for-maxscript-editor/1807

- some properties files can be [found](https://github.com/MerlinEl/Micra/blob/37e40f9d061d53ad81333134f4a75096b4395600/Micra4/App/Maxscript_Settings/dark/MXS_EditorUser.properties) on GitHub, how to install?
- mzp installer doesn't work. installs in correct folder but nothing happens on restart

