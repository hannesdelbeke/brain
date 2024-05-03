
> [!WARNING] 
> This can now be achieved by [[Unity search]].
> ![[Unity tool launcher-1729546910575.jpeg]]
> - Create a search `m: /` ' to show all Menu commands with a `/` (which is all of them).
> - Save the search in the project, e.g. as `Actions.asset`
> - When double clicked it will open the search browser showing all menu commands. User can search at the top.
> 
> if needed you can limit the search to your own tools menu.
> 
> **Drawbacks**
> - When the user uses search, they might accidentally delete the saved search `m: /` which will change the search results. This could confuse the user.
> - No icons supported for menu commands.
## goal
The [[Unity]] main menu, & right-click menu are overwhelming.
A [[tool launcher|command browser]] would hide this clutter.
## tech
plugin infrastructure

mode 1: pure commands
- recreate all default unity menu commands. e.g. open project settings
- custom commands. e.g. launch my editor tool (this can also be a menu command)

mode 2: right click commands in asset browser
right click shows a lot of commands in the project browser, to the point where it's overwhelming and fills the whole screen.
instead show an option that says "browse commands"
this opens a command browser with commands that run on that directory
### features
- [[search bar]]
- [[favorite]]
- [[categorize]]
- option to add custom commands

[[Unity tool]]

[[research existing unity command launchers]]