Currently, I always wrap a tool in a [[wrapper plugin]], publishing it in its own GitHub [[repository|repo]].
However, for a lot of tools, this feels like a waste. Many tools are just [[Python package]]s, that can be imported and installed as [[dependencies]]. And all the plugin usually contain only some code to add a launch command to the menu. It feels silly to make an almost empty repo.

I want to create a [[plugget package]], that doesn't point to a repo, but instead defines: 
- a dependency on a [[Python pip|pip]] package (the published tool),
- a launch command, that then can be run from the plugget UI.

- This way plugget could become a central [[tool launcher]].
- Tools would be instantly accessible, unlike e.g.  [[Unreal plugin|unreal plugins]] which require unreal to restart before you can use them.
- no time is wasted creating skeleton wrapper plugins. (Though, you still need to set up a [[plugget manifest]] ), and less code maintenance. Also less code complexity.
	- [[pip qt]] has been wrapped in 3 different repos, it'd be great if we can avoid this.
		- [[pip Qt Unreal plugin]]
		- [[Maya Pip Qt plugin]]
		- [[Blender pip Qt addon]]

I can use [[plugget action|plugget actions]] to define launch commands.
The [[plugget manifest]] supports actions and dependencies.
And right-clicking on the name in [[plugget qt]] lets the user run any defined action.

## Plan
An example of defining a custom action in plugget: [[plugget - define an action in the manifest]]
An example of defining custom dependencies [[plugget - define dependencies in the manifest]]
A tool I can use to test. Let's wrap the example clock in `PySide6_Examples`
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
## Dev Log
- Defined a [[plugget manifest]] for the clock demo: https://github.com/plugget/plugget-pkgs/tree/main/unreal/pyside6-clock-demo 
- [x] plugget needs some updates to support a repo url of `None`
- dependencies are plugget depencendies, not pip python dependencies.
- [[plugget add support for pip dependencies]]
- still getting problems installing the dependencies. `PySide6_examples` tries to install `PySide6` which is already in use by the plugget qt tool. [[py-pip]] doesn't install already installed tools, however it doesn't handle dependencies of dependencies atm.
  For now, I manually installed this package, which then let me install it through plugget.
- The widget now shows and instantly disappears because it's garbage collected. Command execution is done with `exec`, in a local scope. Setting the widget to global fixes this.

we now have a bit messy but working first pass. The manifest:
```json
{
    "docs_url": "https://doc.qt.io/qtforpython-6/examples/example_gui_analogclock.html",
    "actions": [
        {
            "label": "Show clock",
            "command": "from PySide6.QtGui import QGuiApplication;import PySide6.examples.gui.analogclock.main as main;app = QGuiApplication.instance() or QGuiApplication();global clock; clock = main.AnalogClockWindow();clock.show()"
        }
    ],
    "install_actions" : [
        {
            "name": "unreal_requirements",
            "kwargs": 
            {
                "requirements": ["PySide6_Examples"]
            }
        }
    ]
}
```
## todo 
- make the embedded code more user friendly
	- make the embedded dependencies more user friendly
- can we rely on a unreal-qt plugget package, likely less conflict with PySide6
  figure out a way to rely on other plugget packages in a modular way.
  while those packages handle startup code, and e.g. a modular way to hookup widgets.
- The `dependencies` is confusing, I already mixed them up. 
	- The `pyproject.toml` defines `dependencies`, which are pip dependencies. 
	- The plugget manifest defines `dependencies`, which are plugget dependencies, and `requirements` would be pip dependencies.
- [ ] commands are available, even before the dependencies are installed. which errors
# Goal
- [ ] Create a requirements shortcut
- [ ] add support for more readable command
```json
{
    "actions": [
        {
            "label": "Show clock",
            "command": [
	            "from PySide6.QtGui import QGuiApplication",
	            "import PySide6.examples.gui.analogclock.main as main",
	            "app = QGuiApplication.instance() or QGuiApplication()",
	            "global clock",
	            "clock = main.AnalogClockWindow()",
	            "clock.show()"
            ]
        }
    ],
    "pip-requirements" : ["PySide6_Examples"]
    ]
}
```

> [!NOTE]- Reduce code in manifest with a Python module
> If it's your own module, even better might be to move [[code]] to a module
> ```python
> from PySide6.QtGui import QGuiApplication
> import PySide6.examples.gui.analogclock.main as main
> 
> app = QGuiApplication.instance() or QGuiApplication()
> global clock
> clock = main.AnalogClockWindow()
> clock.show()
> ```
> and set the module as a dependency, so we can just do
> ```json
> "command": "import my_module; my_module.show_clock()"
> ```
> However, we'd still need wrapper code to handle differences in unreal vs Maya vs blender.
> e.g. hooking up to the parent window, making a widget dockable, adding to the menu ...
> You could also make a [[Python module]] for each dcc, but this is kinda similar to the [[wrapper plugin|wrapper plugins]]

Putting this custom code in plugget, reduces plugins. But it increases relying on plugget. And since not many people use plugget atm, could this mean less tool discovery?
It likely doesn't make any difference, since both approaches require raising awareness online. 

[[tooldev]]