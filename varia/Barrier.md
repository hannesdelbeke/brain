Barrier is a virtual keyboard switcher (KVM) 
KVM stands for "keyboard, video, mouse."

install with [[winget]]
```bat
winget install DebaucheeOpenSourceGroup.Barrier
```

if you get the error 
`# is:openERROR: ssl certificate doesn't exist:`
run this line in cmd: (requires git for windows installed)
```BAT
openssl req -x509 -nodes -days 365 -subj /CN=Barrier -newkey rsa:4096 -keyout Barrier.pem -out Barrier.pem
```
source fix: git [issues](https://github.com/debauchee/barrier/issues/231)