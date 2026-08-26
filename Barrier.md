---
sentiment:
- 5
sentiment-hash: 00a43955
sentiment-label:
- factual
tags:
- technical
---

Barrier is a [[virtual]] [[keyboard video mouse|KVM]] to control multiple computers with 1 [[computer mouse|mouse]] and 1 [[keyboard]]. 
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

### Mouse stuck in corner on client (DPI Scaling bug)
When Windows display scaling on the **Server** (or Client) is set above 100% (e.g. 125% or 150%), Barrier's virtual screen coordinate boundary calculation fails, causing the cursor to get trapped / stuck in the bottom corner of the client screen.

Fix:
1. Set Windows display scaling on the **Server** to **100%** (Settings > Display > Scale: 100%).
2. Alternatively: Right-click `barrier.exe` (and `barrierc.exe` / `barriers.exe`) > **Properties** > **Compatibility** > **Change high DPI settings** > Check **"Override high DPI scaling behavior"** > Set to **"Application"**.

[[virtual solution]]
