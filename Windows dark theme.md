Run cmd to enable [[dark mode]] in [[Windows]]
```batch
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f
```

manual toggle
- press windows start 🪟
- type "themes and relates settings"
- click dark theme
