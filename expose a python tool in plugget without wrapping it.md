Currently, I always wrap a tool in a plugin or addon. Publishing it in it's ow [[repository|repo]] on Github.
However, for a lot of tools this feels like a waste. Many tools are just [[Python package]]s, that can be imported and installed as dependencies. And all the plugin usually contain only some code to add a launch command to the menu. It feels silly to make a almost empty repo.

I want to create a plugget package, that doesn't point to a repo, but instead defines: 
- a dependency on a [[Python pip|pip]] package (the published tool),
- a launch command, that the ncan be run from the plugget UI.

- This way plugget could become a central tool launcher.
- Tools would be instantly accessible, unlike e.g.  [[Unreal plugin|unreal plugins]] which require unreal to restart before you can use them.
- no time is wasted creating skeleton wrapper plugins. (Though, you still need to set up a [[plugget manifest]] ), and less code maintenance. Also less code complexity.
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

Let's wrap the example clock in `PySide6_Examples`
```python  
from PySide6.QtGui import QGuiApplication
import PySide6.examples.gui.analogclock.main as main
app = QGuiApplication.instance() or QGuiApplication()
clock = main.AnalogClockWindow()
clock.show()
```

core code
```python  
import PySide6.examples.gui.analogclock.main as main
clock = main.AnalogClockWindow()
clock.show()
```

```
from PySide6.QtGui import QGuiApplication;import PySide6.examples.gui.analogclock.main as main;app = QGuiApplication.instance() or QGuiApplication();clock = main.AnalogClockWindow();clock.show()
```

- Defined a [[plugget manifest]] for the clock demo: https://github.com/plugget/plugget-pkgs/tree/main/unreal/pyside6-clock-demo 
- [x] plugget needs some updates to support a repo url of `None`
- dependencies are plugget depencendies, not pip python dependencies.
- [[plugget add support for pip dependencies]]
- still getting problems installing the dependencies. `PySide6_examples` tries to install `PySide6` which is already in use by the plugget qt tool. [[py-pip]] doesn't install already installed tools, however it doesn't handle dependencies of dependencies atm.
  For now, I manually installed this package, which then let me install it through plugget.
- This kinda works now. But atm the widget instantly disappears because it's garbage collected. Command execution is done with `exec`, so 

[[tooldev]]