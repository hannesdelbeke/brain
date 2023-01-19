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


[official docs](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
on [winget.run](https://winget.run/) & [winstall.app](https://winstall.app/) you can search packages

it's a relatively new (2020) package manager for windows and likely will replace chocolatey & scoop