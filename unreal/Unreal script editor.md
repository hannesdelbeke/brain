[[Unreal]] doesn't yet has a Python script editor
You can download the script editor as an unreal plugin https://github.com/hannesdelbeke/unrealScriptEditor-plugin
Since it's pure python it likely will work in all Unreal versions.

![](https://camo.githubusercontent.com/043f1b6edea7f5e80a6f55f139d623047ed75c12765e25c891a9d387570933f8/68747470733a2f2f692e696d6775722e636f6d2f4b736369786c552e706e67)

> [!Planning]-
> planning notes from before contributing to the tool 
> ### pyqt5
> - we could reuse this PyQt5 widget:[PyEdit2](https://github.com/Axel-Erfurt/PyEdit2)also on [gist](https://gist.github.com/Axel-Erfurt/8c84b5e70a1faf894879cd2ab99118c2)
> 
> ### plugin
> setup the script editor as a unreal plugin
> - auto install dependencies through [[Python pip|pip]]. 
> 	- installing dependencies can be done inside the plugin, similar to the [plugget blender addon](https://github.com/plugget/plugget-blender-addon)
> 	- Or we can use [[plugget|plugget]] or [[Python pip|pip]] to handle the deps
> 
> ### tkinter
> - we could use `tkinter`, which ships with in unreal.
> - [this page](https://realpython.com/python-gui-tkinter/) covers various basics & how to make a tkinter text editor
> ```python
> import tkinter as tk
> window = tk.Tk()
> greeting = tk.Label(text="Hello, Tkinter")
> greeting.pack()
> window.mainloop()
> ```
> see [tkinter in unreal](https://gist.github.com/hannesdelbeke/de3d8d87521ba635b6abd78112ef96bc) gist
> 
> ### other
> The script editor could be dcc independent. E.g. a generic qt widget