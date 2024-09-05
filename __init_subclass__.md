In [[Python]] 3.6 classes now have a init method

```python
class PluginBase:
    subclasses = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.subclasses.append(cls)
```

[source](https://stackoverflow.com/questions/5189232/how-to-auto-register-a-class-when-its-defined/50099920#50099920)