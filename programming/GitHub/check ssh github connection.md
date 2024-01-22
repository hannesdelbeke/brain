to check if the ssh connection on your pc is setup correctly, run in cmd
```bash
ssh -vT git@github.com
```

if not successful and the [[ssh]] key has already been setup
check if the key in `C:\Users\USER\.ssh` is named `id_rsa`
if not rename it, so it'll get automatically picked up.

[[generate SSH key]]