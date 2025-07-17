
```c++
// MyEditorUtilityWidget.h
UCLASS(BlueprintType, Blueprintable)
class MYPROJECT_API UMyEditorUtilityWidget : public UEditorUtilityWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Static Mesh Utils")
    bool GetAutoComputeLODScreenSize(UStaticMesh* StaticMesh)
    {
#if WITH_EDITORONLY_DATA
        if (StaticMesh)
        {
            return StaticMesh->bAutoComputeLODScreenSize;
        }
#endif
        return false;
    }

    UFUNCTION(BlueprintCallable, Category = "Static Mesh Utils")
    void SetAutoComputeLODScreenSize(UStaticMesh* StaticMesh, bool bValue)
    {
#if WITH_EDITORONLY_DATA
        if (StaticMesh)
        {
            StaticMesh->bAutoComputeLODScreenSize = bValue;
            StaticMesh->MarkPackageDirty();
        }
#endif
    }
};
```

use from python
```python
import unreal

# Find your editor utility widget
widget_class = unreal.EditorUtilityWidgetBlueprint.load_asset("/Game/EditorUtilities/MyEditorUtilityWidget")
widget = widget_class.get_generated_class()()

# Use the custom functions
mesh_asset = your_mesh_here
current_value = widget.get_auto_compute_lodscreen_size(mesh_asset)
widget.set_auto_compute_lodscreen_size(mesh_asset, False)
```

[[Unreal C++]]