on windows, you can have 1 folder in 2 places at the same time.
```batch
mklink /j "path_to_copy_folder_to" "path_to_existing_folder"
```

Using `/j` instead of `/d` shows all individual files in source control.
this way code can be shared easily across 2 repos. e.g. when development happens in git, but distribution to artists uses a different source control.

> [!WARNING]
> if you want to delete this link, do not delete it in explorer.
> since this also deletes all content of the original folder.
> instead use 
> ```batch
> rmdir "path_to_link"
> ```
> 
> Pay attention when linking to folders under sourcecontrol, since swapping branches can trigger a folder delete.

It'd be interesting if we could see backlinks in the original folder! #idea


#distribution #repo #path #link