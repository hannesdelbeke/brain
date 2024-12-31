---
aliases:
  - version
---

Handling multiple versions of something, 
often used in [[software development]] with [[dependencies]].

When a release relies on manual updating of a version file, e.g. a toml in python.
It's often forgotten and only noticed when attempting to upload to [[Python Package Index|PyPI]].

Don't rely on manual version updating. 
- Using date versioning this can easily be automated, grabbing the date from the [[version control]] submit.
- if you use [[Semantic Versioning]] this is not the case.