[[Obsidian]] doesn't show up in the expected paths in the [[Windows registry]]
```
HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*
HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*
```

```
Computer\HKEY_USERS\S-1-5-21-974954092-142851879-3959036128-1003\
Software\bd400747-f0c1-5638-a859-982036102edf

Computer\HKEY_USERS\S-1-5-21-974954092-142851879-3959036128-1003\
Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache

Computer\HKEY_USERS\S-1-5-21-974954092-142851879-3959036128-1003\
Software\Classes\obsidian

Computer\HKEY_USERS\S-1-5-21-974954092-142851879-3959036128-1003\
Software\Microsoft\Windows\CurrentVersion\ApplicationAssociationToasts

Computer\HKEY_USERS\S-1-5-21-974954092-142851879-3959036128-1003\
Software\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\AppBadgeUpdated

```

search `C:\Users\hanne\AppData\Local\Obsidian\Uninstall Obsidian.exe`
```
Computer\HKEY_CURRENT_USER\
Software\Microsoft\Windows\CurrentVersion\Uninstall\bd400747-f0c1-5638-a859-982036102edf
Computer\HKEY_USERS\S-1-5-21-974954092-142851879-3959036128-1003\
Software\Microsoft\Windows\CurrentVersion\Uninstall\bd400747-f0c1-5638-a859-982036102edf
```
- `S-1-5-21-974954092-142851879-3959036128-1003` is a [security identifier](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-security-identifiers)
- see [article](https://www.lifewire.com/hkey-users-2625903) on SID
- we can use `Computer\HKEY_CURRENT_USER\` instead of `Computer\HKEY_USERS\S-1-5-21-974954092-142851879-3959036128-1003\`
