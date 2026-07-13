
> [!success] 
> I made my own MCP server in Unreal, see [[2026-02-04 write mcp unreal]]
> - AI can read [[Unreal output log]]
> - and run [[Unreal Python]] in your editor

This came from the idea, I want to ask AI about my Unreal editor, and let it interact with the log. Manually pasting logs into my browser slows me down.
### Existing Unreal MCP servers
Before making a tool, I see if it already exists.
[source](https://www.reddit.com/r/GameDevelopment/comments/1n1fty3/unreal_engine_mcp_how_to_utilize/):
- [kvick-games/UnrealMCP](https://github.com/kvick-games/UnrealMCP) (most established) C++, can run python
- [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) (modern alternative) Python, most stars
- [flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp) (feature-rich)
- [winyunq/UnrealMotionGraphicsMCP](https://github.com/winyunq/UnrealMotionGraphicsMCP) good for basic widget set up

The above MCP plugins create wrapper commands, but don't let your AI run pure python in Unreal.
	*I believed non supported Python commands, but 1 might according reddit.*
### Goal
Can we instead send raw python commands to the [[MCP server|MCP server]]?
e.g. `unreal.EditorLevelLibrary.get_all_level_actors_()`

This would empower your AI tools, and lets you rely on updated docs instead of a non-maintained MCP server repo that needs updating.

### Research and ideas
MCP can pull API from https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorLevelLibrary

Then somehow serialize data, e.g. if type is `StaticMeshActor`
or store it in a cache. Then tell MCP where to find it in the cache
so it can run more commands on it.
```json
{
[
"command": "unreal.EditorLevelLibrary.get_all_level_actors_()",
"result": "var_12345" // reference to cached result in current session
],
[
"command": "for actor in {var_12345}: print(actor.get_name())""
"result": "var_12346"
]
}
```

Or maybe just string based
Send ` "unreal.EditorLevelLibrary.get_all_level_actors_()"`
Receive `["Actor1", "Actor2", "Actor3"]` or exception log

### Test cases
- [x] what actors are in the scene.
	- [x] print list of actor names
- [ ] how much memory does the uasset `scene.uasset` take
	- [ ] find asset, and print memory usage
- [ ] find all references of an asset and tell me the combined memory usage
	- [ ] find asset, find all references, sum memory usage
- [x] duplicate the actor `camera`
	- [ ] 2 assets named camera are found, ask user for more info
	- [ ] user confirms the first one
	- [ ] duplicate the first asset

