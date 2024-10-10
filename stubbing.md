in code stubs are empty code files that only contain all variables.
e.g. 
```python
class FileManager():
	def copy_file(name: str, path: str):
		...
	def delete_file(name: str, path: str):
		...
```
This code does nothing, except tell you which methods it has, and what their arguments are.
This can then be used by your [[integrated development environment|IDE]] to [[autocomplete]] your code during [[programming]], if the library lacks this support by default. E.g. a dynamic library.

[[programming]]