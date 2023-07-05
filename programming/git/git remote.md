
print URLs
```shell
git remote -v
```
```output
origin  https://github.com/hannesdelbeke/unimenu.wiki.git (fetch)
origin  https://github.com/hannesdelbeke/unimenu.wiki.git (push)
```
change URL
```shell
git remote set-url origin https://github.com/USER/git-submodule
```

### Multiple GitHub accounts
to handle multiple hosts. go to config in the folder:
```batch
explorer C:\Users\%username%\.ssh
```

copy the hostname
```
Host github.com
   HostName github.com
   User git
   IdentityFile ~/.ssh/id_rsa
```