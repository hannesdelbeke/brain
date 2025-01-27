[[Samsung Galaxy Tab A8]]


## prep image
- download with SamFirm
- details
	- SM-X200
	- EUX
	- serial/imei R9YT105EDLA
files
- 8gb `AP_X200XXS5DXJ5_X200XXS5DXJ5_MQB87759842_REV00_user_low_ship_MULTI_CERT_meta_OS14.tar.md5`
- 10 Mb `BL_X200XXS5DXJ5_X200XXS5DXJ5_MQB87759842_REV00_user_low_ship_MULTI_CERT.tar.md5`


- There's a hack:
  If [[Odin]] says invalid binary for AP .tar.md5, 
  You can make force load it in Odin if you remove the md5 extension [source](https://www.youtube.com/watch?v=5YaNLDJNnk0) (confirmed)
  But if Odin can't verify the hash, the file is probably corrupt.
  I redownloaded the file (to another hard drive) and then it worked.


- it also failed to load in magisk, but that might be because it needed more disk space on my tablet to make a duplicate of the 8gb, with only 7gb left.
  
  
  
- success with odin (no CSC used though)
```
<ID:0/004> Added!!
<OSM> Enter CS for MD5..
<OSM> Check MD5.. Do not unplug the cable..
<OSM> Please wait..
<OSM> Checking MD5 finished Sucessfully..
<OSM> Leave CS..
<ID:0/004> Odin engine v(ID:3.1401)..
<ID:0/004> File analysis..
<ID:0/004> Total Binary size: 7932 M
<ID:0/004> SetupConnection..
<ID:0/004> Initialzation..
<ID:0/004> Get PIT for mapping..
<ID:0/004> Firmware update start..
<ID:0/004> NAND Write Start!! 
<ID:0/004> SingleDownload.
<ID:0/004> u-boot-spl-16k-sign.bin
<ID:0/004> teecfg-sign.bin
<ID:0/004> sml-sign.bin
<ID:0/004> tos-sign.bin
<ID:0/004> lk-sign.bin
<ID:0/004> sharkl5pro_cm4.bin
<ID:0/004> grd_fw.img
<ID:0/004> super.img
<ID:0/004> boot.img
<ID:0/004> dtbo.img
<ID:0/004> socko.img
<ID:0/004> recovery.img
<ID:0/004> gnssmodem.bin
<ID:0/004> EXEC_KERNEL_IMAGE.bin
<ID:0/004> userdata.img
<ID:0/004> AGCP_DSP.bin
<ID:0/004> vbmeta.img
<ID:0/004> vbmeta_system.img
<ID:0/004> RQT_CLOSE !!
<ID:0/004> RES OK !!
<ID:0/004> Removed!!
<ID:0/004> Remain Port ....  0 
<OSM> All threads completed. (succeed 1 / failed 0)
```
  but fails to start
```
can't load android system. your data may be corrupt. if you continue to get this message, ...
reason is `[fs_mgr_mount_all:M04K00R]`
```


### Prepare your Tablet (only necessary for first install on unrooted device)​

- turn of tablet
	- hold power and volume down 
	- click power off, and confirm
- power up and hold vol up
- select start bootloader

1. install USB drivers on PC
2. unlock OEM
3. flash with odin


[[Samsung Tab A8 - Start Bootloader]]

## Samsung Tab A8 - OEM unlock

### unlock developer options
2. unlock developer options
3. - enable dev mode
	- Settings > About Tablet > Software Information > Click Build Number 7 times quickly

### Allow OEM unlock
- then in Developer Options (just below About Tablet on the left column)
	- Turn on USB Debugging
	- Turn on OEM unlocking (only shows after a software update )

This doesn't unlock the OEM. it allows unlocking the OEM in the next step.
It sets `OEM UNLOCK (L)` to `OEM UNLOCK (U)` t

### Unlock OEM
The OEM unlock screen, is separate from the download screen. ([this img](https://xdaforums.com/t/oem-unlocking-missing.4603847/page-3))
Initially I thought it was the same since it has the same blue background.

I finally managed to get in it with these steps
- [[Samsung Tab A8 - Start Bootloader]]
- cancel (hold 7 sec), this restarts the tablet
- hold both volume buttons with USB plugged in.
	- not sure if it matters, odin is not launched
- follow OEM unlock instructions on the screen. this resets your device again.
### other
- in download mode, you can see the OEM lock state
- [source](https://xdaforums.com/t/guide-sm-t500-t505-galaxy-tab-a7-10-4-unlock-bootloader-root-with-magisk.4185993/) walks you through OEM unlock on another Samsung tablet
## other
[comment](https://stackoverflow.com/a/70178103) mentioning that Samsung devices have no fastboot