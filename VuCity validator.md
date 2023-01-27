A validation tool checks if Maya scenes (city tiles) are set up correctly.
- Success shows as green, fail as red, for a quick visual impression of the scene.
- each check tracks its own status, and can be right-clicked to run actions on it:
	- option to select the meshes or materials that failed `show failed nodes`
	- `check` reruns the check, usefull for when artists attempt to fix issues
	- `fix` attempts to fix the issue if the fix is 100% sure, else error and warn user
- this tool can be batch run on 100s of Maya scenes in the [[VuCity batcher]]

![[VuCity validator-1725549538638.jpeg]]

- UI and functionality are kinda separated in code, but not fully. Since this was written before I learned about [[MVP MVC MVVM compared]]
- It's tightly intertwined with Maya, so not a [[dcc independent]] tool.


existing tile and new tile have different workflows, so different fix buttons

[[Maya tool]]
[[validation]]
[[VuCity]]
