[[Unreal]] doesn't has a native [[Python]] script editor.

You can download the script editor as an [[Unreal plugin]] here: https://github.com/hannesdelbeke/unrealScriptEditor-plugin
Since it's pure Python it should work in all Unreal versions.

![](https://i.imgur.com/KscixlU.png)

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