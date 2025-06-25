By default, [[Unreal]] watches all files in `/Game/` for changes to import.
To exclude a subfolder:
- Go to Editor Preferences: In the Unreal menu, open `Edit > Editor Preferences.`
- Under **General** / **Loading & Saving**, find the **Auto Reimport section**.
- Under `Directories to Monitor`, find the `/Game/` entry, and open the toggle on the left.
- There's a `Include/Exclude Wildcards` toggle with 1 entry: `Localization/*`
- Add your exclude folder here, e.g. `Python/*`, keeping the `include` checkbox is unticked.

> [!example]
> When installing the PySide dependency to the project's python folder, it shows a popup, asking to reimport 1600 json files.
> This example excludes the `Content/Python` folder in your project, so it won't be monitored for changes and ask Unreal to import file changes in there, e.g. `json` files included in Python packages.

[[Unreal Python]]