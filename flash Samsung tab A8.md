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


- if [[Odin]] says invalid binary for AP .tar.md5, remove the md5 extension [source](https://www.youtube.com/watch?v=5YaNLDJNnk0) 
  I confirmed this works
  however if the hash couldn't be verified that could mean something in the file is corrupt.
  it also failed to load in magisk, but that might be because it needed more disk space on my tablet to make a duplicate of the 8gb, with only 7gb left.
  
  
  
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
- enable dev mode
	- Settings > About Tablet > Software Information > Click Build Number 7 times quickly
- then in Developer Options (just below About Tablet on the left column)
	- Turn on USB Debugging
	- Turn on OEM unlocking
- turn of tablet
	- hold power and volume down 
	- click poweer off, and confirm
- power up and hold vol up
- select start bootloader
- 