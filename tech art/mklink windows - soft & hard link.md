## make a symlink
on windows, you can have 1 folder in 2 places at the same time.
```batch
mklink /j "DESTINATION" "SOURCE_FOLDER"
```

Using `/j` instead of `/d` shows all individual files in source control.
this way code can be shared easily across 2 repos. e.g. when development happens in git, but distribution to artists uses a different source control.

## unlink symlink
> [!WARNING]
> if you want to delete this link, do not delete it in explorer.
> since this also deletes all content of the original folder.
> instead use 
> ```batch
> rmdir "path_to_link"
> ```
> 
> Pay attention when linking to folders under sourcecontrol, since swapping branches can trigger a folder delete.

## backlink to original folder
To see backlinks in the folder
print all `symlinks` in a folder, [source](https://superuser.com/questions/823959/how-to-view-all-the-symbolic-links-junction-points-hard-links-in-a-folder-using) 
```batch
dir /al /s
```

to print all `symlinks` for `C:\Users`
⚠️ slow if run on whole PC ⚠️
```powershell
dir 'C:\Users' -recurse -force | ?{$_.LinkType} | select FullName,LinkType,Target
```

### other commands
these commands have some issues where they don't always list all links.

print  `symlinks` on your pc
```batch
cmd /E /C "prompt $T$$ & echo.%TIME%$ & dir /AL /S C:\ | find "SYMLINK" & for %%Z in (.) do rem/ "
```

print `hardlinks`
```powershell
Get-ChildItem -Path "C:\Windows\","c:\","$env:USERPROFILE" -Force |
    Where-Object { $_.LinkType -ne $null -or $_.Attributes -match "ReparsePoint" } |
    ft FullName,Linktype,Target
```


#distribution #repo #path #link