A template for [[Unreal]] Python plugins
https://github.com/hannesdelbeke/unreal-python-plugin-template

features
- it vendors [[py-pip]] so it can auto install dependencies on startup from `requirements.txt`.
  default installs [[unreal-qt]], which installs [[PySide6]]
- includes a demo qt widget
- adds a menu item `tools/myPlugin` to the unreal editor to launch the widget.


- installing PySide to the project triggers import warnings - [[Unreal control which folders to monitor for import|a manual editor fix]]
	- can this be automated?

[startup code](https://github.com/hannesdelbeke/unreal-python-plugin-template/blob/main/MyPlugin/Content/Python/init_unreal.py) to create a [[Unreal editor button]]
- [ ] TODO [[Unreal add menu]]
- [ ] TODO unreal add menu section
## Reference
- https://github.com/laycnc/UnrealExtenstionPluginsTemplates some interesting technical stuff. C++