#### [[Pyblish]] dependency injection
Some functions require their args to be named in certain ways. 
Changing the name of the arg will result in a different value being passed to it. e.g. `context` vs `plugin`.

This feels [[unpythonic]]
A python dev expects the first arg to be passed the first arg. Whereas in [[Pyblish]] the first arg changes the value it get's passed when it's renamed.
The implicit nature of this makes it  hard to understand and debug.