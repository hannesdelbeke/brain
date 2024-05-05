---
aliases:
  - UPM
---
https://docs.unity3d.com/Manual/Packages.html
[[package management]]
[[Unity]]

cons
- doesn't support local package installation like [[pip]] in the user folder.
  Packages are always installed to the project.
  The installed packages are saved to the [[Unity project manifest]].
  Local installs to the project will result in merge conflicts with the project manifest.

opensource projects 
- untested https://github.com/ltmx/Unity.PackageManagerTools
- various packages https://openupm.com/packages/topics/package-management/?sort=downloads