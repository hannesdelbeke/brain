[[Unity tool|Unity editor tools]] don't support a [[menu]] bar by default.
But we can make one ourselves with buttons.

features
- style like a menu
	- option 1: style white like a real menu bar. doesn't match the style IMO
	- option 2: style grey
- tooltips
- submenus
- show context menu under the button, starting at the bottom left corner, not the mouse click position

demo
![[Unity editor menu-1734095279414.jpeg]]
```c#
using UnityEditor;
using UnityEngine;

public class CustomMenuBar : EditorWindow
{
    [MenuItem("Window/Custom Menu Bar")]
    public static void ShowWindow()
    {
        var window = GetWindow<CustomMenuBar>("Custom Menu Bar");
        window.minSize = new Vector2(400, 200);
    }

    private void OnGUI()
    {
        DrawTopBar();
    }

    private void DrawTopBar()
    {
        EditorGUILayout.BeginHorizontal(EditorStyles.toolbar);

        int buttonWidth = 60;

        // File menu
        if (GUILayout.Button("File", EditorStyles.toolbarButton, GUILayout.Width(buttonWidth)))
        {
            ShowContextMenu(new Vector2(0, EditorGUIUtility.singleLineHeight), CreateFileMenu);
        }

        // GUILayout.Space(10);  // empty space

        // Help menu
        if (GUILayout.Button("Help", EditorStyles.toolbarButton, GUILayout.Width(buttonWidth)))
        {
            ShowContextMenu(new Vector2(buttonWidth, EditorGUIUtility.singleLineHeight), CreateHelpMenu);
        }

            
        GUILayout.FlexibleSpace();

        EditorGUILayout.EndHorizontal();
    }

    private void ShowContextMenu(Vector2 position, System.Action<GenericMenu> populateMenu)
    {
        GenericMenu menu = new GenericMenu();
        populateMenu(menu);

        Rect buttonRect = GUILayoutUtility.GetLastRect();
        buttonRect.position += new Vector2(position.x, position.y);
        menu.DropDown(buttonRect);
    }

    private void CreateFileMenu(GenericMenu menu)
    {
        menu.AddItem(new GUIContent("Submenu/Entry1"), false, () => Debug.Log("File > Submenu > Entry1"));
        menu.AddDisabledItem(new GUIContent("Submenu/Entry2"));
        menu.AddSeparator("");
        menu.AddItem(new GUIContent("Exit"), false, () => Debug.Log("File > Exit"));
    }

    private void CreateHelpMenu(GenericMenu menu)
    {
        menu.AddItem(new GUIContent("Menu Item"), false, () => Debug.Log("Help > Menu Item"));
        menu.AddItem(new GUIContent("Submenu/Docs"), false, () => Debug.Log("Help > Submenu > Docs"));
        menu.AddSeparator("");
        menu.AddItem(new GUIContent("About"), false, () => Debug.Log("Help > About"));
    }
}
```
