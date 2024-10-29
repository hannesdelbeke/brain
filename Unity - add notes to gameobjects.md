a [tutorial](https://www.codeproject.com/Tips/1208852/How-to-Add-Comments-Notes-to-a-GameObject-in-Unity) on adding [[note taking|notes]] to [[GameObject|GameObjects]] in the [[Unity inspector]]

1. Create a script called "ThisIsComment". 
   Remove everything from the script and copy the following code to it:
```c#
using UnityEngine;
/// <summary>
/// Attach this script to any gameObject for which you want to put a note.
/// </summary>
public class ThisIsComment : MonoBehaviour
{
    [TextArea]
    public string Notes = "";
    
    void Awake() // destroy this script component in playmode
    {
        Notes = null;
        Destroy(this);
    }
}
```
2. Attach this script to all of the gameObjects to which you want to add note (you can drag this script to the gameObjects or to use "Add Component" button in the corresponding Inspector window). Here is an example:

great for [[documentation]]

Another Unity [thread](https://discussions.unity.com/t/add-info-text-notes-into-the-inspector/548736) describing different approaches. The latest approach is the same as above. 