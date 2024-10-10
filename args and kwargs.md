args and kwargs can be used in Python to pass leftover arguments in a function

## example
```python
def to_uppercase(input):
	return input.upper()
```
we can do `to_upppercase("test")`, but if we do `to_upppercase("test", "123")` our function will break.
Now you might say, the dev messed up, using the code like that. And you are right!

But sometimes we want to support this way of using code, e.g. in abstract functions where you don't know all the ways the user will use the methods. e.g in [[PySide]]
```python
class MyCustomWidget(QtWidgets.QWidget):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
```
In PySide, we can use args and kwargs to pass all arguments supported by QWidget, without having to rewrite them all ourself.
I can still do `MyCustomWidget(parent=my_parent)` without Python throwing an exception.

`*args` catches all undefined arguments (an array)
`***kwargs` catches all undefined keyword arguments (a dict)

[[Python]]
[[software architecture]]