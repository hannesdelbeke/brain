## optimize plugins
I increased startup from 2.2 sec to 0.3 sec by disabling and delaying plugins
- in community plugins, enable debug startup time to see startup time
- disable unused plugins
- use [[Obsidian plugin - Plugin Groups]]
## set priotity to high
No noticeable impact.
save this to a file `obsidian.reg` and run it
```
Windows Registry Editor Version 5.00
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\Obsidian.exe]
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\Obsidian.exe\PerfOptions]
"CpuPriorityClass"=dword:00000003
```


[[Obsidian]]