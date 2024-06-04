When using Python outside the Python path, you get some annoying issues.
I've seen apps load plugins dynamicly, but not add the folders to the path.
this means:
- no support for modules (a folder with python files inside), only a single `.py` file
- the single `.py` file is not importable

offenders:
- [[Maya plugin]]
- [[Pyblish]]
