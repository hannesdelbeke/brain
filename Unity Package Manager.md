---
aliases:
  - UPM
---
https://docs.unity3d.com/Manual/Packages.html
[[package management]]
[[Unity]]

![](https://docs.unity3d.com/uploads/Main/upm-ui.png)

cons
- doesn't support local package installation like [[pip]] in the user folder.
  Packages are always installed to the project.
  The installed packages are saved to the [[Unity project manifest]].
  Local installs to the project will result in merge conflicts with the project manifest.
- no option to favorite packages, and easy install multiple packages from a list.
  the closest is installing those packages, and saving the project manifest somewhere.

opensource projects 
- untested https://github.com/ltmx/Unity.PackageManagerTools
- various packages https://openupm.com/packages/topics/package-management/?sort=downloads