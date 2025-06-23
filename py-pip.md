py-pip lets you install Python packages from inside a Python environment. e.g. in Blender, Maya, Max, ...

The difference with existing solutions, py-pip solves an issue with the environment:
- Blender ships with various python packages pre-installed in it's `python\lib` folder.  
  But pip is not aware of these, e.g. the `venv` package ships with Blender, but when running `pip show venv` it doesn't detect it.  
- Also, any python paths added after Blender startup won't be detected by [[Python pip|pip]]. e.g. various modules in the user site packages are added on startup.  
  If pip can't detect installed packages, it can result in packages being installed twice.

used by
- [[pip qt]]
- [[plugget]]

https://github.com/hannesdelbeke/py-pip

[[my code projects]]