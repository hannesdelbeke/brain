Save this [[Maya MEL|MEL]] code as a `.mel` file.
Drag & drop it in [[Autodesk Maya|Maya]] to print the path of the script.
```c#
global proc FindMe() {}
print("whatIs result -> " + `whatIs "FindMe"` + "\n");
// Mel procedure found in: C:/Folder/test.mel
```
Since it returns a string starting with `Mel procedure found in:`, we have to do some cleanup.
```c#
string $melScriptDir = `substitute "Mel procedure found in: " $melScriptPath ""`;
print($melScriptDir + "\n")
// C:/Folder/test.mel
```
to get the parent folder
```c#
// Remove the file name to get the parent folder ("installer.mel")
$melScriptDir = `dirname $melScriptDir`;
print($melScriptDir + "\n");
// C:/Folder/
```

[[MEL snippet]]

