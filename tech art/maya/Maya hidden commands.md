https://help.autodesk.com/cloudhelp/2022/ENU/Maya-Tech-Docs/CommandsPython/ doesn't list all commands.
`cmds` is dynamic so there's no definitive list.
Any plugin can add new `cmds`. So doing `dir` on the module is the best way to get a list.

In the maya script editor, type `cmds.`, then press ctrl-space to trigger autocomplete, showing the available commands.

`runTimeCommand -commandArray` maybe with `-q` in there should dump all the "not coming from the default commands" (untested)

To output a list of functions (without description)
```python
from maya import cmds
print(dir(cmds))
```

[[Autodesk Maya|Maya]]