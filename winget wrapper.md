wrote this 2023-08-26
An idea to create a python wrapper for the windows package manager, [[winget]].

winget [docs](https://learn.microsoft.com/en-us/windows/package-manager/)
think better with powershell than command
# goal
normal [[winget]] command output
```
>winget list slack
Name  Id                      Version Source
---------------------------------------------
Slack SlackTechnologies.Slack 4.33.90 winget
```

python wrapper
return a class that you can do `.attr` on
```python
apps = winget.list("slack")
slack = apps[0]
slack.name  # Slack
slack.id  # SlackTechnologies.Slack
slack.version  # 4.33.90
slack.source  # winget
```

wrap commands 
- [ ] info	       Displays metadata about the system (version, architecture, log location, etc). 
- [ ] install	Installs the specified application.
- [ ] show	Displays details for the specified application.
- [ ] source	Adds, removes, and updates the winget repositories.
- [ ] search	Searches for an application.
- [ ] list      	Display installed packages.
- [ ] upgrade	Upgrades the given package.
- [ ] uninstall	Uninstalls the given package.
- [ ] hash	Generates the SHA256 hash for the installer.
- [ ] validate	Validates a manifest file for submission to the Windows Package Manager repository.
- [ ] settings	Open settings.
- [ ] features	Shows the status of experimental features.
- [ ] export	Exports a list of the installed packages.
- [ ] import	Installs all the packages in a file.
- [ ] pin	       Manage package pins.
- [ ] configure	Configures the system into a desired state.

- [ ] winget "empty" command (meta)
```batch
winget
```
## reference

- might be able to reference the [[Chocolatey Python API]]
- [winget ui](https://github.com/marticliment/WingetUI) is written in python, see [winget.py](https://github.com/marticliment/WingetUI/blob/main/wingetui/PackageManagers/winget.py)
  can't steal as is, cause UI & functionality are in same file
- WIP [winget python wrapper](https://github.com/emilkloeden/winget)
- [electric](https://github.com/dimensionhq/electric) claims to be better than winget but looks dead 

---
2026-02 not sure of the value on this. I used to be python centric.
likely would be easier now to just rely on the cmd commands etc.
no maintenance, works in multiple languages, and AI just read the winget docs.
i think this was mainly to make my life easier for [[plugget]]
