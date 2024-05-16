## make a symlink
on windows, you can have 1 folder in 2 places at the same time.
```batch
mklink /j "DESTINATION" "SOURCE_FOLDER"
```

For folders, using `/j` instead of `/d` shows all individual files in source control.
this way code can be shared easily across 2 repos. e.g. when development happens in git, but distribution to artists uses a different source control.

> [!options]-
> Without any extra options, `mklink` creates a symbolic link to a file. The below command creates a symbolic, or “**soft**”, link at `Link` pointing to the file `Target` :
> 
> `mklink Link Target`
> 
> Use /D when you want to create a **soft link** pointing to a directory. like so:
> 
> `mklink /D Link Target`
> 
> Use /H when you want to create a **hard link** pointing to a **file**:
> 
> `mklink /H Link Target`
> 
> Use /J to create a **hard link** pointing to a **directory**, also known as a directory junction:
> 
> `mklink /J Link Target`

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

## relative symlinks
you can cd to a directory, and just use folder names to make links relative. don't use C:/ or it will be explicit.
e.g. `mklink /j "vendor" "../vendor"`
both types of slashes are accepted for paths

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


[[Windows]] [[link]] [[file distribution]]