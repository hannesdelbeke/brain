a [tutorial](https://www.codeproject.com/Tips/1208852/How-to-Add-Comments-Notes-to-a-GameObject-in-Unity) on adding [[note taking|notes]] to [[GameObject|GameObjects]] in the [[Unity inspector]]
great for [[documentation]]

1. Create a script called `AssetComments`. 
```c#
using UnityEngine;

#if UNITY_EDITOR
/// <summary>
/// Attach this script to any gameObject for which you want to put a note.
/// </summary>
public class Comment : MonoBehaviour
{
    [TextArea]
    public string Notes = "";
}
#endif
```
2. Attach this script to any gameObjects to which you want to add notes

## disadvantages
- you need to drag the script to each gameObject, instead of instantly typing notes in the inspector.
	- could make some kind of custom importer that adds the script to all gameObjects that don't have it yet.
	- let's make that a custom inspector instead, that adds it to the gameobject as soon as the user writes a note in the inspector.

## tips
- in [[Unity search]] you can search `t:comment`


A Unity [thread](https://discussions.unity.com/t/add-info-text-notes-into-the-inspector/548736) describing different approaches. The latest discussed approach is similar to the above. 