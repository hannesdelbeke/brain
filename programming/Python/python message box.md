Create a simple [[message dialogue]] in [[Python]] without [[Qt]] or dcc code

```python
import ctypes  # An included library with Python install.   
ctypes.windll.user32.MessageBoxW(0, "Your text", "Your title", 1)
```
Styles
```
##  0 : OK
##  1 : OK | Cancel
##  2 : Abort | Retry | Ignore
##  3 : Yes | No | Cancel
##  4 : Yes | No
##  5 : Retry | Cancel 
##  6 : Cancel | Try Again | Continue
```
[source](https://stackoverflow.com/questions/2963263/how-can-i-create-a-simple-message-box-in-python) 

