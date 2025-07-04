---
aliases:
  - primary asset id
---
unreal forums:
> you don’t get Asset ID’s because they don’t exist as a property of static meshes or any other objects. The best you can get is the name of the asset (use `GetDisplayName()` or `GetObjectName()`) - The Python equivalent seems to be `object.get_full_name()`
```python
my_obj: unreal.object
my_obj.get_full_name() # this will return the “unique id” for the object
# get_full_name()→str: get the instance's full name (class name + full path) 
```


