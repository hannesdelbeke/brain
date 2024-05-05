[[Unity]] compiles and initializes code in stages. see [docs](https://docs.unity3d.com/Manual/ScriptCompileOrderFolders.html)

|**Phase**|**Assembly name**|**Script files**|
|---|---|---|
| 1   | Assembly-CSharp-firstpass        | Runtime scripts in folders called Standard Assets, Pro Standard Assets and Plugins.                                                         |
| 2   | Assembly-CSharp-Editor-firstpass | Editor scripts in folders called Editor that are anywhere inside top-level folders called Standard Assets, Pro Standard Assets and Plugins. |
| 3   | Assembly-CSharp                  | All other scripts that are not inside a folder called Editor.                                                                               |
| 4   | Assembly-CSharp-Editor           | All remaining scripts (those that are inside a folder called Editor).                                                                       |

Before compiling user-generated assemblies, Unity compiles `firstpass` code from several folders. 
Unity doesn’t create instance of c# classes in the `firstpass` assemblies, you need tp compile your code into a .dll. 

put the dll in folder `Assets/Plugins/Editor`
[forum source](https://discussions.unity.com/t/add-manifest-json-dependencies-to-exported-unity-package/251910/3)