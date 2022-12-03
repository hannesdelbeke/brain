[[Blender]] preferences contains settings for Blender
e.g. which addons are enabled, your script paths, ...

The preferences are saved in a `userpref.blend`(binary) in the config folder 
```
%AppData%\Blender Foundation\Blender\3.0\config
```

you can print the config folder
```python
bpy.utils.user_resource('CONFIG')
```

- see [stackexchange](https://blender.stackexchange.com/questions/78/how-would-i-import-export-blenders-preferences) 
