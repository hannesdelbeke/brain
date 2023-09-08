### Pyblish action and plugin have no direct link
Pyblish action & plugin have no direct link , instead they find each other through the context.
You can run an action on failed instances, but to get the instance you need to do a bit of hacky code. 
```python
class MyAction(pyblish.api.Action):
    on = "failedOrWarning"

    def process(self, context, plugin):
        for result in context.data['results']:
            if plugin == result["plugin"] and not result["action"]:
                instance = result['instance']
```
A nicer things would be if actions were aware of the instances.
```python
class MyAction(pyblish.api.Action):
    on = "failedOrWarning"

    def process(self, context, plugin):
        for instance in plugin.failed_instances:
            ...
```
Create a bi directional link. actions know their parent plugin, plugins know their instances, instances know their parent plugin, ... and they all know context.