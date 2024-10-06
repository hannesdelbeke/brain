To check if a Python package has been installed, you can use several methods that go beyond just checking if it is importable. Here are some reliable ways to do this:

### Method 1: Using `pip show`

The `pip show` command provides detailed information about an installed package. If the package is installed, it will display information such as the version, location, and dependencies.

```python
import subprocess

def is_package_installed(package_name):
    try:
        result = subprocess.run(['pip', 'show', package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except Exception as e:
        return False

# Example usage:
package_name = 'numpy'
if is_package_installed(package_name):
    print(f"{package_name} is installed.")
else:
    print(f"{package_name} is not installed.")

```

### DEPRECATED ~~Method 2: Using `pkg_resources`~~

The `pkg_resources` module from `setuptools` can be used to check if a package is installed and get its version.

```python
import pkg_resources

def is_package_installed(package_name):
    try:
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False

# Example usage:
package_name = 'numpy'
if is_package_installed(package_name):
    print(f"{package_name} is installed.")
else:
    print(f"{package_name} is not installed.")
```

### Method 2: Using `importlib.metadata`
```python
import importlib.metadata

def is_package_installed(package_name):
    try:
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False

# Example usage:
package_name = 'numpy'
if is_package_installed(package_name):
    print(f"{package_name} is installed.")
else:
    print(f"{package_name} is not installed.")
```

### Method 3: Using `importlib.util.find_spec`

Although you mentioned that you don't want to just check if it's importable, this method can still be used in combination with other checks to ensure the package is indeed installed.

```python
import importlib.util

def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None

# Example usage:
package_name = 'numpy'
if is_package_installed(package_name):
    print(f"{package_name} is installed.")
else:
    print(f"{package_name} is not installed.")
```

### Method 4: Using `pip list`

You can list all installed packages and check if the desired package is in the list.

```python
import subprocess

def is_package_installed(package_name):
    try:
        result = subprocess.run(['pip', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return package_name in result.stdout
    except Exception as e:
        return False

# Example usage:
package_name = 'numpy'
if is_package_installed(package_name):
    print(f"{package_name} is installed.")
else:
    print(f"{package_name} is not installed.")
```

Each of these methods has its own advantages, and you can choose the one that best fits your specific needs. For a more robust solution, combining a couple of these methods can provide additional assurance.

[[Python stubs-]]
[[Python snippet]]