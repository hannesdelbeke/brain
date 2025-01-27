
you can start the bootloader, even if you don't have the bootloader "unlocked"
when you are in the bootloader, you ll see OEM LOCK ON, which means it's locked


aliasses:
- bootloader
- download mode
- odin mode



## Samsung Tab A8 - Start Bootloader - download mode
you can either start it manually from the tablet, or with a adb command
### manual
- launch the menu (2 options)
	- hold volume up volume down, and meanwhile connect the usb cable
	- or hold power + vol down
- select restart to bootloader
- you now see the blue downloader screen
### command
[source](https://source.android.com/docs/core/architecture/bootloader/locking_unlocking)
- install adb
- enable developer settings & USB debugging
- connect USB cable to pc. ensure you have samsung USB drivers installed
- drag down the top menu bar and select USB settings, change to something then back to filetransfer.
- a popup should appear, click accept to let computer control tablet.
run in cmd
```
adb reboot bootloader
```

