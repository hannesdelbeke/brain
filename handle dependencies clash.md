If 2 packages in your project use different versions of the same dependency, you can't use both packages simultaneously.

package A -> import package C v1
package B -> import package C v2

you can't use A & B together

```python
# package A
import test
test.print()  # should print v1
```

```python
# package B
import test
test.print()  # should print v2
```

```python
# package C v1
def print():
    print("v1")
```

```python
# package C v2
def print():
    print("v2")
```

### other

a custom import handler, which registers where to import from for which package
could solve this ❌
- once imported, python wont try reimport this module for the other module.
- we can also overwrite the module cache

[[package management]]