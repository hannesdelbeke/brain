winget allows quick app install on windows from a terminal.

> [!Example]+
> This command will install slack, notion, discord & miro.
> Simply copy & paste it in your command prompt
> 
> ```batch
> winget install --id=SlackTechnologies.Slack -e && winget install --id=Notion.Notion -e && winget install --id=Discord.Discord -e && winget install --id=Miro.Miro -e
> ```
> ![[install.gif]]

## Install winget

#### Install winget through the Microsoft store.

- open the windows store from the start menu, and search for [app installer](ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1)
- or run this command to open the **app installer** store page
```batch
start ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1
```

- Search app installer, and install this app
- open a new terminal and run the command: `winget`

### Other
[official docs](https://learn.microsoft.com/en-us/windows/package-manager/winget/)

it's a relatively new (2020) [[package management|package manager]] for [[windows]] and likely will replace chocolatey & scoop. Atm [[Chocolatey]] is still more capable IMO

it's by default included in [[windows 11]].
- it won't work in cmd until after a few windows updates.
- the installed version is old and has issues. update `app installer` in the Microsoft store. (this eventually will auto update in the background.)

update all Microsoft Store apps
```powershell
 Get-AppxPackage -AllUsers | foreach { Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\AppXManifest.xml" }
```
### Create new distributions
quickly create installation scripts for public software on
-   https://winstall.app/
-   https://winget.run/
