Until now, I was setting up projects like this:
Menus in a project are created with [[unimenu]], by hooking up code as a string in a [[yaml]] config.
```
🗒️ plugin.py
📁 scripts
-- 📁 resources
-- -- 🗒️ menu.yaml
```

## code string
However, code as a string is less direct. 
`code string` -- (convert to callable code) --> `code`
- you can't easily browse to module definition in your [[integrated development environment|IDE]].
- when you [[refactor]], the code in the strings isn't updated.
- no syntax coloring for your coding language.

If we distribute code, we might as well keep it as a python file.
I think using a config is more of a thing I just did without thinking about it, because "everyone" did this, or other devs in the past told me to. I just never questioned it.

It'd be nicer to set up a [[python module]] that defines the [[menu]]. Distributing code as code.
Better IDE support to browse & edit the code

## resources loading
Since a python module can just be imported, It also means we don't need to load resources, Which feels unintuitive. 
The loading of resources is a less direct link. 
- We can't easily browse to the config in this setup, we have to manually do so. 
- The menu config feels buried in our Maya library, we have to remember where it lives (more [[cognitive load]], or read the code to figure out.
- Code doesn't update correctly during [[refactor]]
```python
import unimenu
menu_config_path = files("my_maya_scripts.resources") / 'menu.yaml
unimenu.setup(menu_config_path)
```

With an import, the [[integrated development environment|IDE]] can just instantly browse to it. [[Code]] updates during [[refactor]], and it's more [[pythonic]] and [[cognitive ease|simpler to understand]]. ([[keep it simple|KISS]])
```python
import unimenu
import my_menu
my_menu.setup()
```
## refactor
We have a [[maya plugin]] in a separate folder from our maya scripts. 
The resources folder is in the maya scripts folder. 

So for menu generation we have: 
`plugin` trigger menu creation -> load `resource` path in plugin (which lives in scripts) -> go back to `plugin` to create menu

and for menu code hookup we have
`config` string code -> `scripts` code

we need to keep both of these links in mind while editing code, or the hookup might break.
This is too much [[cognitive load]], requiring your mind to jump forward and back. Even as the author it always takes some time to wrap my head around.

I prefer to keep all menu code contained separate from the plugin code ([[separation of concerns]]), I'll put it in scripts. . 
```
🗒️ plugin.py
📁 scripts
-- 🗒️ menu.py
```

For a more [[portable]] approach (e.g. when distributing outside a project), just [[copy paste]] all menu code directly in the plugin. Now the maya plugin contains all code to make the menu. 
```
🗒️ plugin.py
```
## review
the end result is simple python code, with full IDE support
no need to learn about resources
no need to learn yaml syntax
no complex structure to keep in your head while editing code


[[software architecture]]