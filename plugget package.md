---
aliases:
  - plugget packages
---
A [[package]] for [[plugget]]

A plugget package is basically a [[plugget manifest]].

The difference is that the package describes the concept of a manifest and it's files.
But unlike e.g. python wheels, there's no actual package like a zip file containing both files and manifest. The files are often downloaded afterward, based on data in the manifest.
So you get both of them during install, but from a different source.
So behind the curtains it's not a package, but what the user sees looks like installing one.