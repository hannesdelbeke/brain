Currently, I always wrap a tool in a plugin or addon. Publishing it in it's ow [[repository|repo]] on Github.
However, for a lot of tools this feels like a waste. Many tools are just [[Python package]]s, that can be imported and installed as dependencies. And all the plugin usually contain only some code to add a launch command to the menu. It feels silly to make a almost empty repo.

I want to create a plugget package, that doesn't point to a repo, but instead defines: 
- a dependency on a [[Python pip|pip]] package (the published tool),
- a launch command, that the ncan be run from the plugget UI.

- This way plugget could become a central tool launcher.
- Tools would be instantly accessible, unlike e.g.  [[Unreal plugin|unreal plugins]] which require unreal to restart before you can use them.
- no time is wasted creating skeleton wrapper plugins. (Though, you still need to set up a [[plugget manifest]] ), and less code maintenance. Also less code,complexity.
	- [[pip qt]] has been wrapped in 3 different repos, it'd be great if we can avoid this.
		- [[pip Qt Unreal plugin]]
		- [[Maya Pip Qt plugin]]
		- [[Blender pip Qt addon]]

I can use [[plugget action|plugget actions]] to define launch commands.
The [[plugget manifest]] supports actions and dependencies.
And right-clicking on the name in [[plugget qt]] lets the user run any defined action.

An example of defining a custom action in plugget: [[plugget - define an action in the manifest]]
An example of defining custom dependencies [[plugget - define dependencies in the manifest]]
A tool I can use to test.
	make 2 versions; [[pip Qt Unreal plugin]]
	and a new pip qt wrapper package



[[tooldev]]