1. view your current network configuration
```batch
ipconfig /all
```

2. add static ip, change name if needed. e.g. "Ethernet 2"
```
netsh interface ip set address name="Ethernet" static 192.168.1.100 255.255.255.0 192.168.1.1
```

delete settings TODO, work this out
```
netsh interface ip delete address name="Ethernet"
```

## Manual
1. you can also go to `network connections`
2. righ click ethernet, properties
3. set ipv4 properties
4. set the ip address etc

DNS can be set to 1.1.1.1 (google)
