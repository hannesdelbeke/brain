see [docs](https://docs.unrealengine.com/4.27/en-US/PythonAPI/class/_ObjectBase.html#unreal._ObjectBase)

get all [[Unreal]] actors in scene
```python
import unreal
actorSub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# get all actor names
names = [x.get_name() for x in unreal.EditorLevelLibrary.get_all_level_actors()]
```

blog [getting_started_with_python_in_ue4](https://sondreutheim.com/post/getting_started_with_python_in_ue4)
- Enabling the plugin
- Python in the editor
- Adding your own scripts
- Autocomplete in VS Code
- Importing assets
- Managing [[Unreal Blueprints Visual Scripting|blueprints]]

An object’s “Outer” is the object which “owns” it. For instance, a Component is owned by its Actor or parent component, and Actors are owned by their Levels. Whenever you construct an object of a class derived from UObject, you provide it with an Outer. (CreateDefaultSubobject implicitly provides the current object as the Outer.)
[source](https://forums.unrealengine.com/t/how-can-i-understand-the-data-member-outer-in-the-uobjectbase-class/330196)

docs unreal [assettools](https://docs.unrealengine.com/4.26/en-US/PythonAPI/class/AssetTools.html#unreal.AssetTools) to dynamically create assets

Python [tutorial](https://www.freecodecamp.org/news/becoming-an-unreal-automation-expert/#writing-our-own-automated-project-clean-up-script-using-python) to batch move assets to a new folder. A simple short intro on the basics but not much else.

[thread](https://forums.unrealengine.com/t/creating-blueprint-assets-hierarchies-with-python/115929/16) that discusses adding components with python dynamically, solution for blueprints.