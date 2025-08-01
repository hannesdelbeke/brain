## Question
i want to vendor a python module "[[plugget]]" with a plugin, plugget can install other python modules

i want it to install itself if there is a more recent version. if it does so, it would have to reload the python modules. would a simple del imported modules with name contain plugget do this? are there other recommended ways? what are the pros and cons. i know a simple reload doesn't always does the trick for some reason.

also, how can i ensure it wont try to import the outdated plugget that is vendored with the plugin?
## Answer 

### Reloading `plugget` After Self-Upgrade

Using `del sys.modules[name]` to remove `plugget` from the module cache **won’t fully reset the state** if other modules or objects still hold references to it. Here’s why:
- **Pros**:
    - It forces Python to re-import the module from disk.
    - It’s simple and works in many basic cases.
- **Cons**:
    - Any ==existing references== (e.g. `from plugget import something`) will still point to the old version.
    - Dependencies of `plugget` won’t be reloaded unless you explicitly do so.
    - It can lead to subtle bugs if the module maintains internal state or caches.

A more robust approach is:
```python
import sys
import importlib

if 'plugget' in sys.modules:
    importlib.reload(sys.modules['plugget'])
else:
    import plugget
```

But even `importlib.reload()` has limitations:
- It re-executes the module’s code but **doesn’t update ==existing references==**.
- It doesn’t reload submodules or dependencies unless you do that manually.

---
### Avoiding the Vendored Version
To ensure Python doesn’t import the outdated vendored `plugget`, you can:
1. **Manipulate `sys.path`**:
    - Insert the path to the updated `plugget` (e.g. from site-packages) **before** the vendored path.
    - Or remove the vendored path entirely if the update succeeds.
2. **Use `importlib.util.find_spec()`** to inspect where the module is coming from:
    ```python
    import importlib.util
    spec = importlib.util.find_spec("plugget")
    print(spec.origin)  # Check if it's the vendored one
    ```
3. **Namespace isolation**:
    - Consider using a subprocess to run the plugin logic with a clean import environment.
    - This avoids the complexity of in-process reloading altogether.
      ==I could add the vendor folder to python path, import and install, then remove from path==
4. ==I could vendor the module under a different name, e.g. plugget_vendored==
---
### Final Thoughts
consider:
- Designing it to be stateless or restart-safe.
- Using subprocesses or even `importlib.machinery.SourceFileLoader` to load a fresh copy under a different name.
# Notes
- plugget's `_requirements.py` action already vendors [[py-pip]], see [code](https://github.com/plugget/plugget/blob/9e46d4f7588e0818adb25eb52665a1c666a93696/plugget/actions/_requirements.py#L11)
  `_utils.py` doesn't use the vendored version, but the import is wrapped in a local method so it should be fine.
  This approach doesn't handle any module reload.
- This could work for unreal plugins, but [[Blender addon|Blender addons]] & [[Maya plugin|Maya plugins]] aren't in the PATH so only support a single python file. This requires a copy paste code solution, or dynamic adding to the pwath. At least maya has a workaround with [[Maya module]]s but it'd be nice to have it for plugins too.
- the [[Maya plugin template]] already has an installer, so we can use this. (I think the installer already installs dependencies)
- The new [[Blender extension]] support vendoring dependencies, so lets ignore [[Blender addon]]