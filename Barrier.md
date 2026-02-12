Barrier is a [[virtual]] [[keyboard video mouse|KVM]] to control multiple computers with 1 mouse and 1 keyboard. 
When moving your cursor of the side of 1 screen, it appears on other computer's screen. It's just like having 2 screens attached to 1 computer, with the difference that instead you control 2 computers.

*KVM stands for "keyboard, video, mouse."*

> [!winget install]- 
> install with [[winget]]
> ```batch
> winget install DebaucheeOpenSourceGroup.Barrier
> ```

## Bugs
### ssl certificate doesn't exist
if you get the error `# is:openERROR: ssl certificate doesn't exist:`
```Powershell
Set-Alias openssl "C:\Program Files\Git\usr\bin\openssl.exe"
cd ~\AppData\Local\Barrier\SSL\
openssl req -x509 -nodes -days 365 -subj /CN=Barrier -newkey rsa:4096 -keyout Barrier.pem -out Barrier.pem
```
[source](https://github.com/debauchee/barrier/issues/231#issuecomment-1143791895) 
### Barrier - log says failed to start server
install older version
```
winget uninstall barrier
winget install barrier --version 2.3.3-release
```
run barrier, log should show success. 
quit barrier and update
```
winget upgrade barrier
```

### VPN support
If you use a pc with [[virtual private network|VPN]], barrier won't work.
But you can connect first to barrier, and then the VPN. And your barrier connection should stay active without the VPN

### Barrier stops when asking admin permission
1. open Barrier's settings
2. change elevated from `as needed`(default) to `always`.

[[virtual solution]]