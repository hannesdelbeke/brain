---
aliases:
  - env var
  - env vars
---
An environment variable is a variable that's accessible to your whole environment.
It is often used to control software. 

## Examples
Adding a path to the `PATH` variable, adds a search path for all apps using this (Console, Python, ...)

When setting `MY_ENV_VAR` to `hello world` on Windows, any app launched will inherit this variable.
After launching Blender, Max or Maya, they all can access that variable in Python like this:
```python
import os
env_var = os.environ['MY_ENV_VAR']#
print(env_var)  # prints "hello world"
```

Note that on Windows, env variables are always strings.