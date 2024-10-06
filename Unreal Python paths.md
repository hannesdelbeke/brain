Let's explore [[Python]] paths for importing Python modules in [[Unreal]].
## site paths
```
site.getsitepackages()
'../../../Engine/Binaries/ThirdParty/Python3/Win64'
'../../../Engine/Binaries/ThirdParty/Python3/Win64\\Lib\\site-packages'
```
both of these folders are added to sys.path by Unreal

```
site.getusersitepackages()
C:\Users\H\AppData\Roaming\Python\Python311\site-packages
```
This folder doesn't exist atm
## sys.path
paths (in import order)

> [!NOTE]- Unreal editor paths
> unreal install folder `D:\\Program Files\\Epic Games\\UE_5.4\\Engine`
> ```
> Engine\\Binaries\\ThirdParty\\Python3\\Win64\\python311.zip
> Engine\\Binaries\\ThirdParty\\Python3\\Win64\\DLLs
> Engine\\Binaries\\ThirdParty\\Python3\\Win64\\Lib
> Engine\\Binaries\\Win64
> Engine\\Binaries\\ThirdParty\\Python3\\Win64
> Engine\\Binaries\\ThirdParty\\Python3\\Win64\\Lib\\site-packages
> ```

> [!NOTE]- Unreal project paths
> project Python folder
> ```
> MYPROJECT/Content/Python
> ```
> 
> project site packages
> ```
> MYPROJECT\\Content\\Python\\Lib\\site-packages 
> ```
> 
> project plugin python paths
> ```
> MYPROJECT/Plugins/python-script-editor/PythonScriptEditor/Content/Python
> MYPROJECT/Plugins/hello-world-template/MyPlugin/Content/Python
> MYPROJECT/Plugins/texture-browser/TextureBrowser/Content/Python
> MYPROJECT/Plugins/unreal-qt/UnrealQt/Content/Python 
> MYPROJECT/Plugins/Pyblish/Content/Python
> MYPROJECT/Plugins/Plugget/Content/Python
> ```

> [!NOTE]- Unreal editor default plugin paths
> unreal install folder plugins `D:/Program Files/Epic Games/UE_5.4/Engine`
> ```
> Engine/Plugins/MovieScene/SequencerScripting/Content/Python
> Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python
> Engine/Plugins/Animation/IKRig/Content/Python
> Engine/Plugins/Animation/ControlRig/Content/Python
> ```

> [!NOTE]- other paths
> project site packages (again) #TODO figure out why split in 2.
> ```
> MYPROJECT\\Intermediate\\PipInstall\\Lib\\site-packages 
> MYPROJECT\\Content\\Python\\Lib\\site-packages\\unreal_script_editor\\..
> ```
> other, likely manual path manipulation from script?
> ```
> D:\\repos\\plugget
> ```
## Broken or unused paths?
I discovered a folder 
```
%LOCALAPPDATA%\UnrealEngine\5.4\Content
```
Which, it being a `Content` folder, implies we can do `Content/Python`, since Unreal auto handles all `Python` folders in a `Content` folder. 
```
%LOCALAPPDATA%\UnrealEngine\5.4\Content\Python\Lib\site-packages
```
But modules in there are not importable, and the path is not added to site packages

There's also 
```
%LOCALAPPDATA%\UnrealEngine\5.4\Intermediate\PipInstall\Lib\site-packages
```
Which contains an empty [[pth|.pth]] file, implying site packages usage.
But currently this is not hooked up I believe, unless it's related to this somehow?
```
MYPROJECT\\Intermediate\\PipInstall\\Lib\\site-packages 
```
