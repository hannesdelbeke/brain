for editor windows, don't use init. it seems to lead to weird repaint bugs in the editor.
sometimes text is drawn twice over each other.
not sure if caused by this 


```c#
static void Init()
{
	var window = GetWindow<NoteEditor>("Note Editor");
	window.Show();
}

```

use this instead
```c#
public static void ShowWindow()
{
    GetWindow<NoteEditor>("Note Editor");
}
```
