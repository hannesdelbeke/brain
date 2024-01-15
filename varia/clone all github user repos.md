1. cd to the folder to clone
2. run command in shell or gitbash
```shell
GHUSER=CHANGEME; curl "https://api.github.com/users/$GHUSER/repos?per_page=1000" | grep -o 'git@[^"]*' | xargs -L1 git clone
```

to clone private repos, set the token [here](https://github.com/settings/tokens) and in the command
```shell
GHUSER=CHANGEME; GITHUB_API_TOKEN=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; curl -s "https://api.github.com/users/hannesdelbeke/repos?access_token=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&per_page=1000" | grep -w clone_url | grep -o '[^"]\+://.\+.git' | xargs -L1 git clone
```

tested on Windows
[source](https://stackoverflow.com/questions/19576742/how-to-clone-all-repos-at-once-from-github)