---
aliases:
  - .venv
---

https://docs.python.org/3/library/venv.html

- Used to contain a specific Python interpreter and packages / modules, isolated from the ones installed on the system
- Contained in a directory, e.g. `.venv` or `venv`,  `~/.virtualenvs`.
- Considered as disposable – easy to recreate from scratch.
- Not movable or copyable

## Create
to create a new [[virtual environment]]:
```batch
python -m venv /path/to/new/virtual/environment
```

## Use
A virtual environment may be “activated” using a script in its binary directory 
- `bin` on POSIX
- `Scripts` on Windows

**how it works:**
This prepends that directory to your `PATH`, so that running `python` invokes the environment’s Python interpreter instead of the system one.

[[environment management]]
[[Python]]
[[Python env management]]
