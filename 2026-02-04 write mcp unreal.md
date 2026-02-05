
## Challenge
I want [[OpenCode]] to talk directly with [[unreal]] (through an [[MCP server]]) 

- read output [[log]] from unreal
  *Copy pasting the log from unreal to [[copilot]] every time i ask for advice is time consuming. I reduced the [[mental resistance|mental friction]] and made this workflow smoother.*
  
- send [[Unreal Python]] commands
  *It might be dangerous in a production environment to enable a LLM to run code in your project. But it also can be very powerfull. Mixed with some good version control, the user should be able to do this safely in a branch or fork.* 

---
## Ideas
### 1. python plugin
forward log output to an [[MCP server]]
### 2. read from file on disk
could be a simple text instruction for the AI that people copy past. e.g.
> output log lives in this location `C:\Users\Unreal\Logs\game.log`
> read the last 100 lines of this file only.
### 3. existing MCP servers
There are some existing MCP plugins. Not sure if they expose Unreal's log
it's more structured commands, actors, BPs, ...
And no support to run python commands

---
## Progress
I ended up writing a [[Unreal Python]] mcp [[Unreal plugin|plugin]] in 3 hours with [[GPT 5.2]]
It combines a python plugin with reading from the log file on disk.
It can also run py commands.

https://github.com/hannesdelbeke/py-mcp-unreal
- forward log output to mcp server
- enable AI to run python commands in unreal