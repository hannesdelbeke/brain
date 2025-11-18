---
aliases:
  - usersetup
  - usersetup.py
---

> [!warning]
> I recommend to use [[Maya plugin]] to run startup code, and not use usersetup.

Any file named `usersetup.py` will be run by [[Maya Python]] interpreter on [[Maya run on startup|Maya startup]].
## How it works
It loops over all the paths and calls `exec` on any `usersetup.py` files it finds.

## Cons
### Startup exceptions
Since there isn't any error handling, any errors in usersetup will prevent any other usersetups from loading.

If you use [[Maya module|Maya modules]] with usersetup, and one of them fails, other modules might fail to load.
- [ ] TODO create a sample

AFAIK startup code in [[Maya plugin||Maya plugins]] is cleaner, and doesn't run into this issue. The affected plugin is simply disabled.

### Messy environment
Often tools rely on editing the usersetup in `Documents/Maya/scripts`. This is not recommended, because it might clash with other tools.

E.g. an outsource studio who works for 2 clients installs your tools, which overwrite the `usersetup.py` from the other studio.

### Security risk flagging
Since Maya 2022+, running `userSetup.py` on startup can be disabled. Or you might get a popup asking for confirmation if you want to run it. 
- [ ] AFAIK plugins do not have this issue. confirm this.

