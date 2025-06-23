---
aliases:
  - portable plugget
---
figure out how i can vendor a lightweight version of [[plugget]] with plugins
so devs can create self installing plugins and addons. without asking the user to install plugget first.

main goal:
- create an easy solution to create plugins that auto self-install dependencies
## Increase plugget exposure for devs
This way devs can integrate plugget in their plugins to make dependency installation easier for users. But they can do it behind the scenes, so they can take the credit. And it doesn't feel like I'm forcing plugget on them, like a door to door salesman.

Meanwhile, plugget adoption will increase with devs. The increased adoption might lead to increased popularity, and convince devs to add their tool to the plugget ecosystem. 
But it wouldn't increase plugget users, so it's a low impact change.
## todo
- [ ] vendor a version of plugget.
- [ ] ensure import plugget only uses the vendored version if plugget is not installed
- is it possible to only ship dcc related actions? only a few bytes so likely not worth it.
- [ ] ensure plugget first tries to update itself (and reloads itself), before installing dependencies

example plugins that could use a self install, so user can just copy paste the plugin folder
- [[pip Qt Unreal plugin]]
- [[Unreal Python script editor]]