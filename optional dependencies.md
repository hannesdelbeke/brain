Aim for minimum dependencies, where possible make them optional. Making your tools more robust.

If your qt tool works better with an additional qt-manager like [[BQt]] or [[unreal-qt]], instead of adding it as a dependency, make it an optional dependency.

If your tool relies on icons for it's buttons, fall back on text if the icons can't be found. Avoiding situations such as: your tool still works but the icon's don't show. [sample](https://github.com/leixingyu/unrealScriptEditor/issues/3)
- avoid the classic "[it works on my pc](https://donthitsave.com/comic/2016/07/15/it-works-on-my-computer)"

PyPi supports [optional dependencies](https://setuptools.pypa.io/en/latest/userguide/dependency_management.html). Letting you choose to install them during the [[python pip|pip]] install.