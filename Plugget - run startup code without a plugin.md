## Goal
The goal is to run startup code, without creating an (Unreal) [[wrapper plugin]] for each tool.
e.g. startup code could be to set up [[unreal-qt]]
## Notes
This is an idea / brainstorm, startup code is not yet implemented in the [[plugget manifest]].
Plugget does run a [[Unreal plugin]]'s startup code after installation.

Maybe we can have a dynamic Unreal plugin that runs startup code.
It's a single plugin, some kind of manager.

---
Suggestion to add startup_code, instead of a repo_url.
So we can distribute pure commands, this is similar to [[expose a python tool in plugget without wrapping it]]

config
```json
{
startup_code: "import tool;tool.show()"
}
```

Startup code makes sense if there is no `repo_url`
but if there is, does startup code replace it?

1. create unreal plugin
2. add startup code to `init_unreal.py`
## cons
The current plugget approach for unreal start up code, is specific to unreal plugins.
So plugget needs a dynamic plugin action for every dcc app.
- We could create a generic system, but then plugget possibly becomes a environment manager, handling startup code instead of only installations.
- is there at least an option to create a single unreal plugin, where you register startup code? this could be plugget or a separate plugin.

[[plugget Unreal]]