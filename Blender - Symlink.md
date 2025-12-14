To make code from external repositories importable in blender, you can create a symlink to Blender's scripts folder.

To create the symlink, see [[mklink windows - soft & hard link|instructions for Windows]].
Blender add-ons live in roaming, see `%AppData%` in [[Windows environment variables|windows env variables]], e.g.
`C:/Users/hannes/AppData/Roaming/Blender Foundation/Blender/4.0/scripts/addons`

pros
- least effort, just run 1 line of code in the terminal once
- stays in your environment between Blender sessions
- works with any python module. Not just addons or python packages
cons
- creates issues with [[git]], if git tries to delete the link e.g. when changing branch
