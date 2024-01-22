Barrier is a virtual keyboard switcher (KVM) to control multiple computers with 1 mouse and 1 keyboard. 
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
run this: (requires [[bash on windows]])
```shell
openssl req -x509 -nodes -days 365 -subj /CN=Barrier -newkey rsa:4096 -keyout Barrier.pem -out Barrier.pem
```
source fix: git [issues](https://github.com/debauchee/barrier/issues/231)