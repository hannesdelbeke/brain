#### [[Pyblish]] dependency injection
Some functions require their args to be named in certain ways. 
Changing the name of the arg will result in a different value being passed to it. e.g. `context` vs `plugin`.

This feels [[unpythonic]]
A python dev expects the first arg to be passed the first arg. Whereas in [[Pyblish]] the first arg changes the value it get's passed when it's renamed.
The implicit nature of this makes it  hard to understand and debug.

### variable name controls plugin behavior
changing the name of the arg changes the plugin behavior.
```python
class ValidateSceneTriCount(pyblish.api.ContextPlugin):
    order = pyblish.api.CollectorOrder
    def process(self, context):
	    ...
```

this will run process once, like expected from a collector
```python
    def process(self, context):
	    ...
```

this runs context on every instance that's collected. when refactoring your code from a validator to a collector, this is an easy thing to miss. and it doesn't error out. 
```python
    def process(self, instance):
	    ...
```