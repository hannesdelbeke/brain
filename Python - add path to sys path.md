When you want to test a [[python package]] or [[Python module|module]] that's not importable, you can manually add it to the [[Python sys path|sys path]].

1. add to path
```python
import sys
sys.path.append('/path/to/directory')
```
2. import and test
```python
import my_module
```

[[Python env management]]
[[Python stubs]]