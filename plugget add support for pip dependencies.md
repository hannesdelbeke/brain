default actions in `package.py` define install instructions
```python
def default_install_actions(self):  
    """get the default action for the app"""  
    # to prevent install bugs, ensure the dependencies install before the main plugin/addon  
    # so order pip-install actions (requirements) in the list before addon-install actions,    DefaultInstallActions = {  
        "blender": ["blender_requirements", "blender_addon"],  
        "max3ds": ["max3ds_requirements", "max3ds_macroscript"],  
        "maya": ["maya_requirements", "maya_plugin"],  
        "krita": ["krita_requirements", "krita_plugin"],  
        "unreal": ["unreal_requirements", "unreal_plugin"],  
        "substance_painter": ["substance_painter_requirements", "substance_painter_plugin"],  
    }  
    install_actions = DefaultInstallActions.get(self.app)  
    if not install_actions:  
        raise Exception(f"no default action for app '{self.app}'")  
    return install_actions
```

we can add a new action to install python dependencies, if defined in the [[plugget manifest]]
