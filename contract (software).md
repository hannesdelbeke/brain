---
aliases:
  - contract
---
a contract defines what to expect. 
so you don't have to read all the underlying code to know what it will do.
this reduces [[cognitive load]]

examples
- a image class always has a load and a save method.
  now a dev can use `jpgImage` and `bmpImage` and knows it can use `.save()` on both.
- a method always returns a certain datatype. e.g. `load_image()` returns type  `Image`

[[programming]]