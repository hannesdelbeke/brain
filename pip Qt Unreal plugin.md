---
aliases:
  - pip for unreal UI
---
A UI to see installed python packages in [[Unreal]], and search, uninstall & install packages.
repo: https://github.com/hannesdelbeke/pip-qt-unreal

## TODO
atm it requires a manual installation of dependencies, or a [[plugget]] install
It'd be nice if the plugin could install its own dependencies.
[[plugget - create a self-installing plugin]]

- [ ] Similar to [[plugget UI to show dependencies]] to see dependencies would be *great* 

## tech
It's a [[Unreal plugin]] that adds a launch command for [[pip qt]] to the menu.
## dependencies
- [[unreal-qt]] for QT UI in Unreal
- [[pip qt]] to show or download python packages
