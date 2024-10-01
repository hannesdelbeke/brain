describe the wrapping of an existing mel plugin, and the issues i ran in.

First I created a repo from the [[Maya plugin template]]
I wrote a README and added credits and image, before testing the code.
I assumed it would work since it was released.

Then I realized I should test it first. So I follow the instructions and find out there are some bugs in the code. I fix the bugs 
- Y & Z procs are just copy pasted from X, but not renamed
- there is some clipping in the UI
- When I try run it from python or using `source` in [[Maya MEL|mel]], i notice the non global procs don't work. I convert them to global.
- When I add the file in the maya script path, and run it from mel with the script name, it doesn't work because there's a `.` in the name. convert this to `_` fixes that.
I now have the plugin working and it can be run from a command.
And this mel code runs the script if directly under a Maya `scripts` folder
```javascript
source "Created_controls_1_01.mel";
```

I hook the mel script up to a python plugin with `maya.mel.eval()`.

But I realize I have 2 files, and a [[Maya plugin]] only supports a single Python file.
So let's convert this package to a [[Maya module]].
I use my [[Maya module template]] to make a new repo.

After hooking up my module to maya with a local env var edit to add the path to `MAYA_MODULE_PATH`, the plugin shows in maya, adds a menu entry. And clicking it launches the tool.

But the icons are missing, and the fbx-es dont spawn when clicked. 
Something is wrong with the path.
Turns out the mod file env var was not correctly set. 

now works and launches. packaging done.