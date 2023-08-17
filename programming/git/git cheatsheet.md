[[git]]

change date
```bash
git commit --amend --date="3 day ago" --no-edit
git commit --amend --date="20 July 16:00" --no-edit
```

- `:q!` to finish the commit in console

change author
```bash
git commit --amend --author="hannes <hannes@address.com>" --no-edit
```

batch rename author from commit, [source](https://stackoverflow.com/questions/750172/how-do-i-change-the-author-and-committer-name-email-for-multiple-commits)
```bash
git rebase -r 32873fa26ea2e5068bbf489693cdceed8abdf0d8 --exec 'git commit --amend --no-edit --reset-author'
```

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