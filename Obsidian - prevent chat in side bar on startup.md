
### Problem
When I start [[Obsidian]], it shows the copilot Chat in the right sidebar.
- A distracting yellow warning was added to the chat window.
- It states some people were banned using chat, so I rather not use it.
### Context
I already disabled the [[obsidian-copilot]] plugin a few days ago to hide the chat window, so I was surprised it showed up again.
It turns out that [[obsidian-plugin-groups]] enables the plugin on startup, overriding my manual disabling of said plugin, which was an unexpected consequence of [[Obsidian faster startup|increasing Obsidian startup times]].
### Solution
To not show the chat window on startup
- Edit the [[obsidian-plugin-groups|plugin group]] config to not enable the copilot plugin
- or uninstall the [[obsidian-copilot]] plugin.
### Unexpected plugin behavior
I closed all right side windows/tabs, and restarted Obsidian. Obsidian remembered the side window state on restart, so it didn't show after restart.
The side window showing on startup wasn't because of the copilot plugin, but because I had a side panel open when I closed Obsidian.

After manually expanding the side window to show it, the chat window appears again (if the [[obsidian-copilot]] plugin is enabled). 
So if the chat is closed in a previous session, [[obsidian-copilot]] reopens the chat on startup. But it doesn't override the side window's visibility state.

So when using another plugin on the right side window, it won't show that same window after restart. Instead, the copilot plugin loads the chat window, resulting in a [[unintuitive]] experience for the user. This feels like [[implicit]] plugin behavior. You can't expect a user to close the right window every time they close Obsidian. Therefor this is not a realistic solution to the problem.