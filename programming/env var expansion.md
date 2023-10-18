On Windows, ``%name%`` expansion is also supported in addition to `$name` and `${name}` expansion.

On Windows:
```python
# set env var TEST = 8
os.path.expandvars("${TEST}")
# '${TEST}' if env var not found
# '8' prints value of env var if found
```

Linux uses `${vari}`

- [[Python]] `expandvars` [article](https://www.geeksforgeeks.org/python-os-path-expandvars-method/)