Currently, I always wrap a tool in a plugin or addon. Publishing it in it's ow [[repository|repo]] on Github.
However, for a lot of tools this feels like a waste. Many tools are just [[Python package]]s, that can be imported and installed as dependencies. And all the plugin usually contain only some code to add a launch command to the menu. It feels silly to make a almost empty repo.

I want to create a plugget package, that doesn't point to a repo, but instead defines: 
- a dependency on a [[Python pip|pip]] package (the published tool),
- a launch command, that the ncan be run from the plugget UI.

- This way plugget could become a central tool launcher.
- Tools would be instantly accessible, unlike e.g.  [[Unreal plugin|unreal plugins]] which require unreal to restart before you can use them.
- no time is wasted creating skeleton wrapper plugins. (still need to setup a plugget manifest though)

I can use [[plugget action|plugget actions]] to define launch commands.
The [[plugget manifest]] supports actions and dependencies.
And right clicking on the name in [[plugget qt]] lets the user run any defined action.

an example of defining a custom action in plugget: [[plugget - define an action in the manifest]]
an example of defining custom dependencies [[plugget - define dependencies in the manifest]]
a tool i can use to test.
	make 2 versions; [[pip Qt Unreal plugin]]
	and a new pip qt wrapper package



[[tooldev]]