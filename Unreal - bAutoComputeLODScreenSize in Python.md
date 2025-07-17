```python
mesh_asset.get_editor_property("bAutoComputeLODScreenSize")
# LogPython: Error: Exception: StaticMesh: Property 'bAutoComputeLODScreenSize' for attribute 'bAutoComputeLODScreenSize' on 'StaticMesh' is protected and cannot be read
```

The var `bAutoComputeLODScreenSize` seems to be public in the [[Unreal C++]] source code in `Engine\Source\Runtime\Engine\Classes\Engine\StaticMesh.h` 
```c++

#if WITH_EDITORONLY_DATA
...
public:

	int32 GetLightmapUVVersion() const
	{
		WaitUntilAsyncPropertyReleased(EStaticMeshAsyncProperties::LightmapUVVersion);
		PRAGMA_DISABLE_DEPRECATION_WARNINGS
		return LightmapUVVersion;
		PRAGMA_ENABLE_DEPRECATION_WARNINGS
	}

	/** If true, the screen sizes at which LODs swap are computed automatically. */
	UPROPERTY()
	uint8 bAutoComputeLODScreenSize : 1;
```
The reason you were getting the "protected and cannot be read" error is because Python reflection in Unreal Engine respects the [[C++]] access modifiers and preprocessor directives. Since `bAutoComputeLODScreenSize` is within `#if WITH_EDITORONLY_DATA`, it's not exposed to the Python API directly, even though it appears to be in a public: section.

But there's a blueprint callable
```c++
#if WITH_EDITOR
	UFUNCTION(BlueprintCallable, Category = StaticMesh)
	bool IsLODScreenSizeAutoComputed() const
	{
		return bAutoComputeLODScreenSize;
	}
#endif
```

in [[Unreal Python]] it can be accessed with 
```python
mesh_asset.is_lod_screen_size_auto_computed()  # False
```

## TODO hack
An approach that might give us access to protected vars: [[LLM recommend a custom C++ Unreal editor tool - untested]]
