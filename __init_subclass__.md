In [[Python]] 3.6 classes now have a init method
this makes implementing the [[registry pattern]] easier.

```python
class PluginBase:
    subclasses = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.subclasses.append(cls)
```
any plugin that inherits from PluginBase will add itself to the subclasses list. 
AFAIK the only condition is that the code is imported (and therefor runs the class definition)

[source](https://stackoverflow.com/questions/5189232/how-to-auto-register-a-class-when-its-defined/50099920#50099920)
[[Python snippet]]