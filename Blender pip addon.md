A [[Python]] module manager for [[Blender]], using [[Python pip|pip]]
Get it from the [GitHub repo](https://github.com/hannesdelbeke/blender_pip)

### new repo
https://github.com/hannesdelbeke/blender_pip
- [x] pass paths to [[Python pip|pip]]
- [x] install to user modules folder unique for each blender version
- [x] support editable install for local repos by auto adding a script that handles `site dir` in startup folder (which likely doesn't exist)
      [[Blender doesn't support editable Python packages]]

Original author pointed out this should be tested  on Linux and Mac, currently Windows only. AFAIK it should work on other OS.

### original repo
https://github.com/amb/blender_pip
issues:
- doesn't [[pass custom sys.paths to subprocess]]. So pip isn't aware of some modules Blender discovers on startup. So some installed modules don't show up in `pip list`, or can't be removed with `pip uninstall`, see [PR](https://github.com/amb/blender_pip/pull/11)
- packages are installed to site packages, which are shared between different blender versions. Not a great workflow. [PR](https://github.com/amb/blender_pip/pull/10)
- installing editable packages to a target directory doesn't work since `.pth` files don't live in `site dir`, see [[Blender doesn't support editable Python packages]]

[[Blender addon]]
[[package management]]
