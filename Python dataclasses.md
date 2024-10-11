A data class is a lightweight version of a class, used as a data container.

`__post_init__` runs after the default init, and can be used to add extra attributes

```python
from dataclasses import dataclass

@dataclass
class MyClass:
	name: str
	color: tuple
	
	def __post_init__(self):
		self.capitalized_name = self.name.upper()
```

[[Python]]