a demo [[Maya module]] definition file

> [!WARNING] 
> the sample on the Autodesk website incorrectly states `plugins` instead of `plug-ins`

```
+ MAYAVERSION:2023 PLATFORM:linux <ModuleName> <ModuleVersion> <ModulePath> 
[r] plugins: <non_default_path_to_plugins>
[r] scripts: <non_default_path_to_scripts>
PATH+:=<path_to_add>

+ MAYAVERSION:2023 PLATFORM:mac <ModuleName> <ModuleVersion> <ModulePath> 
[r] plugins: <non_default_path_to_plugins>
[r] scripts: <non_default_path_to_scripts>
PATH+:=<path_to_add>
```