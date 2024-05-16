### pip README emoji bug
[[BQt]] bug
emoji in README.md crashes the [[Python pip-|pip]] install with git+
changing the line in setup.py to this fixes that.  [source](https://stackoverflow.com/questions/49640513/unicodedecodeerror-charmap-codec-cant-decode-byte-0x9d-in-position-x-charac)
```python
long_description = (this_directory / "README.md").read_text(encoding="utf-8")
```
