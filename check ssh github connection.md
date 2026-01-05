to check if the ssh connection on your pc is setup correctly, run in cmd
```bash
ssh -vT git@github.com
```

if not successful 
- if no ssh
	- [[generate SSH key]]
	- add ssh to github 
- if the [[Secure File Transfer Protocol|SSH]] key has already been setup, check if the key in `C:\Users\USER\.ssh` is named `id_rsa`
command to browse to the folder:
```cmd
explorer %USERPROFILE%\.ssh
```

if not rename your key to `id_rsa`, so it'll get automatically picked up.

[[GitHub]]
[[Windows]]
[[git]]