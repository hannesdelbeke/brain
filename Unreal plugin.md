---
aliases:
  - unreal plugins
  - uplugin
---
A [[plugin]] for [[Unreal]].
To install a Unreal plugin, place your plugin folder either in engine, or in project folder

- [[package management]] is local only.
  Unreal is mostly designed to work with Perforce. Which takes care of this.
- Wrote own *package* manager for Unreal: [[plugget Unreal]]

## Pros
- modular, easy to enable/disable
## cons
- enabling a plugin requires a restart of Unreal, there's no reason this is needed for content-only plugins, but it's required atm.
	- For [[pure Python]] plugins it should be possible to create a workaround. I think [[plugget]] does so.

## todo
- figure out if it supports multiple context:
  can be set in editor, or project, or local to user (with [[gitignore]]/perforce ignore))

You can enable the plugin _just for yourself_ without modifying the `.uproject` file by editing the plugin’s `.uplugin` file like this:

```json
"EnabledByDefault": true,
"Installed": false
```
This tells Unreal to treat the plugin as enabled by default (for your local engine), but not to mark it as installed in the project — so it won’t get written into the project’s plugin list or synced via Perforce.

- Navigate to the plugin’s folder (usually under `Engine/Plugins/`).
- Open the `.uplugin` file in a text editor & modify the fields.

Only use this for **editor-only plugins**.


