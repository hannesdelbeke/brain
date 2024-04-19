```python
import unreal


# Example usage
asset_path = "/Game/Curves"
curve_name = "MyLinearColorCurve"


# Function to create a linear color curve and save it
def create_curve(asset_path, curve_name):
    # create_linear_color_curve
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    curve_factory = unreal.CurveLinearColorFactory()
    asset_name = curve_name
    asset_package_path = asset_path
    new_curve_asset = asset_tools.create_asset(asset_name, asset_package_path, unreal.CurveLinearColor, curve_factory)
    if not new_curve_asset:
        unreal.log_error("Failed to create the color curve asset.")
        return None

    time_key_points = [0.2, 0.7]
    color_values = [0.8, 0.3]
    for time, color in zip(time_key_points, color_values):
        new_curve_asset.add_key(unreal.ColourChannel.RED, time, color)  # channel, time value / this is not a native unreal method

    package = new_curve_asset.get_outer()
    unreal.EditorAssetLibrary.save_asset(asset_package_path + "/" + asset_name, only_if_is_dirty=True)
    unreal.log("Color curve asset created and saved successfully.")
    return new_curve_asset

```

[[linear color curve]]
[[Python stubs]]
[[Unreal Python]]