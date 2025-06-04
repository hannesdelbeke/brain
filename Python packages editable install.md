---
aliases:
  - editable install
---

An editable install, creates a [[symbolic link|symlink]] between the source code of a Python package and the Python environment, allowing you to modify the source code without needing to reinstall the package.
(AFAIK this breaks and requires a reinstall when changing [[versioning|version]] of your package)

### how to

1. find out where to install the python packages, for the app you are targeting. e.g.
```
C:\Users\H\AppData\Local\UnrealEngine\5.4\Intermediate\PipInstall\Lib\site-packages

```

2. this command edit installs (see local install with [[Python pip]])
You'll need a target to chose where to install it. And `SomeProject` is the package.
```
python -m pip install -e path/to/SomeProject --target "C:\Users\H\AppData\Local\UnrealEngine\5.4\Intermediate\PipInstall\Lib\site-packages"
```

