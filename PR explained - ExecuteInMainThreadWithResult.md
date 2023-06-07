---
sentiment:
- 5
sentiment-hash: 140a4d0e
sentiment-label:
- factual
tags:
- technical
- work
---

explain PR https://github.com/pyblish/pyblish-unreal/pull/6
[[Unreal Python]]
This is not [[pure Python]], since it's C++

---

The `executeInMainThreadWithResult` method in this Unreal Engine plugin is a **custom Python extension function** that allows you to **execute a Python function on Unreal’s main (game) thread** and return the result back to your Python script.
### 🔧 Why is this needed?
Unreal Engine is **not thread-safe** for many operations — especially ones that interact with the Editor or Game world (e.g., spawning actors, changing assets, UI updates). So when running Python code from outside the main thread (e.g., from a background task, or Python environment), you must ensure such calls are **executed on the main thread**.
### ✅ What does it do exactly?
Let’s break it down.
#### ✅ Function signature
```cpp
static PyObject* ExecuteInMainThreadWithResult(PyObject* ModuleSelf, PyObject* InArgs, PyObject* InKwargs)
```
- `InArgs`: A Python tuple, where the first item is the function (callable), and the rest are its positional arguments.
- `InKwargs`: Any keyword arguments (a Python dict).
#### ✅ What it does
1. **Saves the current Python thread state** using `PyEval_SaveThread()` — important for releasing the GIL (Global Interpreter Lock) so other Python threads can run while waiting.
2. **Creates an Unreal async task** using `FFunctionGraphTask::CreateAndDispatchWhenReady(...)` which:
    - Switches to the **main (game) thread** using `ENamedThreads::GameThread`
    - Restores Python's GIL via `PyGILState_Ensure()`
    - Calls the Python function (`PyObject_Call`) with provided args and kwargs
    - Stores the result in `Result`
    - Releases the GIL with `PyGILState_Release()`
3. **Waits for the main thread task to complete** using `FTaskGraphInterface::Get().WaitUntilTaskCompletes(Task);`
4. **Restores the original Python thread state** with `PyEval_RestoreThread(...)`
5. **Returns the result** of the Python function back to the caller.
### 🧪 Example
```python
import unreal

def my_python_function(a, b):
    return a + b

result = unreal.executeInMainThreadWithResult((my_python_function, 3, 4))
print(result)  # -> 7
```

Or using kwargs:
```python
def myfunc(a, b, c=10):
    return a + b + c

res = unreal.executeInMainThreadWithResult((myfunc, 1, 2), {'c': 5})
print(res)  # -> 8
```
### ⚠️ Limitations / Notes
- The callable and its args **must be pickle-safe and Python-callable**.
- This assumes you are running Python code with Unreal’s Python integration.
- If you pass an invalid function or arguments, it may crash or silently fail.
- Any function you call must not block indefinitely — it’s running on the game thread!
### 🔗 Regarding Pyblish

The author said:

> "目前它尚未连接到此 repo 中的 pyblish。 我们该如何连接它？"

Translation:

> _"Currently it's not yet connected to the Pyblish in this repo. How should we connect it?"_

So the plugin just adds this main-thread-callable support for now — and doesn’t integrate with [[Pyblish]] yet. You’d need to add code that uses `executeInMainThreadWithResult` in your Pyblish plugin callbacks if you want to safely trigger Unreal operations from within a Pyblish process.

## How is it different from running python directly?
> but i can run unreal code perfectly fine on it's own in python.
> that s what import unreal is for, so what does this plugin do extra?

It’s a subtle but important distinction.

> **✅ Yes** — when you're in Unreal's built-in Python environment (like the script editor or a Python Console tab), `import unreal` works and you can run `unreal` API calls **directly**.

So then:

> **❓ What does this plugin actually do extra, if `unreal` works already?**
### 🔍 The key difference: **Thread safety**
When you run Python in Unreal (e.g., via the console or script editor), it already **runs on the main game thread**, so there's no problem calling `unreal.EditorAssetLibrary`, `unreal.EditorLevelLibrary`, or similar.

But this only applies **in very specific contexts** — usually **interactive sessions** or tightly sandboxed scripts.
#### 🧵 What if you're in another thread?
If you're running:
- From **Pyblish**
- A **background Python thread**
- A **scheduled coroutine**
- An **external tool communicating with Unreal**
- **Parallel tasks** (multi-threaded pipeline steps)

Then **you're not on the main thread**, and many Unreal API calls will:
- Crash
- Hang
- Fail silently
- Throw “must be called from game thread” errors
### 🧩 What this plugin adds
This plugin lets you **explicitly and safely execute arbitrary Python code on Unreal’s main thread**, from anywhere — even if your current Python context is not on the main thread.

It gives you:
```python
unreal.executeInMainThreadWithResult((callable, arg1, arg2), {'kwarg': val})
```
This is **not part of default Unreal Python API** — it’s custom. Epic's Python integration doesn’t expose this utility natively.

|Context|Default `unreal` API|This plugin's `executeInMainThreadWithResult`|
|---|---|---|
|Unreal Python console|✅ works|✅ also works (but not needed)|
|Pyblish plugins|❌ unsafe|✅ makes it safe|
|Background Python thread|❌ unsafe|✅ safe|
|External Python tool talking to Unreal|❌ risky|✅ useful for bridging|
### 🧠 Summary
The plugin doesn’t change how you normally run Python in Unreal, **but it gives you a safe tool** when you're working from places that **don’t guarantee the main thread**, such as automated tools, pipelines, or threaded workflows.

If you're running Pyblish from inside Unreal — or sending Python over sockets or subprocesses — this tool becomes necessary.
