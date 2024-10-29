
a bit hacky atm.
- it's very slow since it updates every character.
- it has issues with applying the saved note to the next selected folder. since atm it doesnt remember the last selected folder. and on selection changed it things the folder path is the new selected folder.

```C#
using UnityEditor;
using UnityEngine;
using VoxelBusters.CoreLibrary;

[InitializeOnLoad]
public class FolderNoteEditor : Editor
{
    // Tracks the path of the selected folder
    static string previousSelectedFolderPath = "";
    static string selectedFolderPath = "";

    static FolderNoteEditor()
    {
        Debug.Log("init");
        Selection.selectionChanged += OnSelectionChanged;
    }

    private static void OnSelectionChanged()
    {
        Debug.Log("Selection changed");

        // Check if the selected object is a folder
        string path = AssetDatabase.GetAssetPath(Selection.activeObject);
        if (AssetDatabase.IsValidFolder(path))
        {
            selectedFolderPath = path;
        }
        else
        {
            selectedFolderPath = "";
        }
    }

    [CustomEditor(typeof(DefaultAsset))]
    public class FolderInspector : Editor
    {
        // This will hold the current note for the selected folder
        private string folderNote = "";

        private void OnEnable()
        {
            LoadNote();
        }

        public override void OnInspectorGUI()
        {
            // Check if the selected object is a folder
            if (AssetDatabase.IsValidFolder(AssetDatabase.GetAssetPath(target)))
            {
                EditorGUI.EndDisabledGroup();  // HACK to work around Unity disabling UI elements in the inspector for folders

                EditorGUILayout.LabelField("Folder Notes", EditorStyles.boldLabel);

                // Text area for the note
                string newNote = EditorGUILayout.TextArea(folderNote, GUILayout.Height(60));

                // Save the note if it’s changed
                if (newNote != folderNote)
                {
                    folderNote = newNote;
                    SaveNote();
                }

                EditorGUI.BeginDisabledGroup(true);

                EditorGUILayout.HelpBox("This note is saved in the folder's .meta file.", MessageType.Info);
            }
            else
            {
                base.OnInspectorGUI();
            }
        }

        private void LoadNote()
        {
            if (!string.IsNullOrEmpty(selectedFolderPath))
            {
                AssetImporter importer = AssetImporter.GetAtPath(selectedFolderPath);
                folderNote = importer.userData;
            }
        }

        private void SaveNote()
        {
            if (!string.IsNullOrEmpty(selectedFolderPath))
            {
                Debug.Log("Saving note: " + folderNote + " for " + selectedFolderPath);
                AssetImporter importer = AssetImporter.GetAtPath(selectedFolderPath);
                importer.userData = folderNote;  // this might clash with other scripts that use userData
                importer.SaveAndReimport();

                // set custom string in the meta file?

                // select the folder again to refresh the inspector
                Selection.activeObject = AssetDatabase.LoadMainAssetAtPath(selectedFolderPath);
            }
        }
    }
}

```