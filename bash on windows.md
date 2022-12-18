by default windows does not ship with bash. To add bash support:

1. install [git for windows](https://gitforwindows.org/) 
```powershell
winget install git.git
```

2. add `C:\Program Files\Git\bin\` to the environment variable PATH

you can test that it worked by running `cmd` and typing `bash`,
if installed successfully it displays a blinking $

3. restart Obsidian, you now can run bash code with [execute code](https://github.com/twibiral/obsidian-execute-code)