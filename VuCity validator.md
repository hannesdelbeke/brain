A [[validator|validation tool]] checks if Max scenes (city tiles) are set up correctly.
- Success shows as green, fail as red, for a quick visual impression of the scene.
- each check tracks its own status, and can be right-clicked to run actions on it:
	- option to select the meshes or materials that failed `show failed nodes`
	- `check` reruns the check, useful for when artists attempt to fix issues
	- `fix` attempts to fix the issue if the fix is 100% sure, else error and warn user
- this tool can be batch run on 100s of Max scenes in the [[VuCity batcher]]

![[VuCity validator-1725549538638.jpeg|400]]

- UI and functionality were mostly separated in code, but not fully. Since this was written before I learned about [[MVP MVC MVVM compared]]
- It's tightly intertwined with Max, so not a [[dcc independent]] tool.

Existing tiles have different workflows from new tiles, so different fix buttons

[[3ds max tool]]
[[validation]]
[[VuCity]]
