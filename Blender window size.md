why does user32 return a different window size than bpy?

```python
import ctypes
from bqt.blender_applications.win32_blender_application import get_process_hwnds
from ctypes import wintypes  
user32 = ctypes.windll.user32

process_windows = get_process_hwnds()
for win in process_windows:  
	# get height and width  
	rect = wintypes.RECT()  
	user32.GetWindowRect(win.hwnd, ctypes.byref(rect))  
	height = rect.bottom - rect.top  
	width = rect.right - rect.left  
	print(height, width)
  
import bpy  
print("height bpy", bpy.context.window_manager.windows[0].height, "width", bpy.context.window_manager.windows[0].width)

```

| type                     | height | width |
| ------------------------ | ------ | ----- |
| main window user32       | 2065   | 2124  |
| main window bpy          | 2009   | 2102  |
| main window diff         | 56     | 22    |
| -                        |        |       |
| preference window user32 | 913    | 1158  |
| preference window bpy    | 857    | 1136  |
| preference window diff   | 56     | 22    |

when qt wrapped window is 0 height. bpy returns 0
but qt returns 56 height. likely the title bar height
measure with [[Microsoft PowerToys|PowerToys]] returns 28 pixels height
windows, 150% scale on `3840 x 2160px`

[[Blender Python]]