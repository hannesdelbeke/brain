1. open cmd
	1. [[check ssh github connection]]
	2. run `gh auth login`, follow the steps
2. open git bash
	1. cd to the folder to clone
	2. run command in shell or gitbash
```shell
GHUSER=CHANGEME; curl "https://api.github.com/users/$GHUSER/repos?per_page=1000" | grep -o 'git@[^"]*' | xargs -L1 git clone
```

tested on Windows
[source](https://stackoverflow.com/questions/19576742/how-to-clone-all-repos-at-once-from-github)