## always set process priority to high
The example below always starts `obsidian.exe` with high priority.

Save this to a file `obsidian.reg` and [[as admin|as admin]].
```
Windows Registry Editor Version 5.00
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\Obsidian.exe]
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\Obsidian.exe\PerfOptions]
"CpuPriorityClass"=dword:00000003
```
[source](https://answers.microsoft.com/en-us/windows/forum/all/how-to-permanently-set-priority-processes-using/df82bd40-ce52-4b84-af34-4d93da17d079)