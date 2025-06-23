the [plugget unreal plugin - code at the time](https://github.com/plugget/plugget-unreal-plugin/blob/623971957862f0d810a33c11cc84cca8922b427d/Plugget/Content/Python/init_unreal.py)

it ships with no vendored code
if [[plugget qt]]  isn't installed, it tries to pip install from `git+https://github.com/plugget/plugget-qt`

it uses hardcoded install logic instead of plugget install logic
- target project site packages. `'C:/Users/USER/MyProject/Content/Python/Lib/site-packages'
- [[importlib - invalidate caches]]
- print log to [[unreal console]]

cons
- it runs pip in the command line on first install, so might not work if python not installed.
  [[Unreal]] ships with pip, but not sure if added to PATH in unreal's environment
	- [ ] can we update this to use Unreal's py-interpeter? instead of pip `unreal.get_interpreter_executable_path()`

relates to [[plugget - create a self-installing plugin]]
