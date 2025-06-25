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
## dev plan
- [x] vendor a version of plugget.
- [x] ensure import plugget only uses the vendored version if plugget is not installed
- is it possible to only ship dcc related actions? only a few bytes so likely not worth it.
- [x] ensure plugget first tries to update itself (and reloads itself), before installing dependencies
## dev log
- [[plugget - create a self-installing plugin brainstorm]]
- achieved all above plugget features in [[Unreal python plugin template]]
- replaced plugget vendor with [[py-pip]], a simpler solution for Unreal. Less good for plugget.
  The reason to use plugget was to avoid having to rewrite custom installers for each dcc.
  But plugget has more dependencies (e.g. `requests`) increasing vendor size to 3 Mb.
- remove self updating logic of vendored modules
# todo
get a working solution for other dcc. maya/blender.


Add self installer to 
- [[pip Qt Unreal plugin]]
- [[Unreal Python script editor]]
- [[Unreal texture browser plugin]]
- [[plugget Unreal plugin]]
- ~~[[unreal-qt plugin]]~~

