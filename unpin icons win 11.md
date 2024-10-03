To unpin all [[icon|icons]] from the [[Windows task bar]] (⚠️ not the [[Windows start menu]]) in [[Windows 11]]:
```batch
DEL /F /S /Q /A "%AppData%\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\*"

REG DELETE HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband /F

taskkill /F /IM explorer.exe & start explorer
```

don't confuse with [[unpin start menu icons win 11]]