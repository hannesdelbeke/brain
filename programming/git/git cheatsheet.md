[[git]]

change date
```bash
git commit --amend --date="3 day ago"
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