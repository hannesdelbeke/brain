## Challenges
writing a custom class takes time
using a dict is too primitive, and has no [[autocomplete|autocomplete]].

sample config, can be loaded with [[Python config loader utils-]]
```YAML
my_settings:
  - key1: value1
  - key2: value2
  - key3: value3
```

```python
class MySettings:
	def __init__(self):
		self.key1 = value1
		self.key2 = value2
		self.key3 = value3
```
But ideally the class can be dynamically create, passing the values to `__init__`.
```python
class MySettings:
	def __init__(self, key1=None, key2=None, key3=None):
		# we use `or` since mutatible values (e.g. strings) 
		# can't be used as kwarg default values
		self.key1 = key1 or value1
		self.key2 = key2 or value2
		self.key3 = key3 or value3
```
With `*args` & `**kwargs`, attribute values can be dynamically loaded with `setattr`, but then we loose IDE auto complete.

Another option could be to create the class with empty args and let the user fill them in after instance creation.

When the class is only used in a config loader, it can make sense to pass the config as a single value instead.
```python
class MySettings:
	def __init__(self, config_dict):
		...
```

#### other
But now every time the config is updated, the python class needs updating.

## other

alternatives?
- investigate dataclass
- typed dict

see
- [how-do-i-convert-a-json-file-to-a-python-class](https://stackoverflow.com/questions/69773539/how-do-i-convert-a-json-file-to-a-python-class)
- [convert-json-data-into-custom-python-object](https://pynative.com/python-convert-json-data-into-custom-python-object/) JSONEncoder/decoder + custom class
- https://levelup.gitconnected.com/how-to-deserialize-json-to-custom-class-objects-in-python-d8b92949cd3b


#deserialize

[[Python]]
[[config]]