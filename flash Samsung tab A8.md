[[Samsung Galaxy Tab A8]]
claims that certain version of bootloader doesn't allow flashing [here](https://www.reddit.com/r/LineageOS/comments/119nz5t/bootloader_version_not_compatible_with/)

## prep image
- download with [[SamFirm]]
- details
	- SM-X200
	- EUX
	- serial/imei R9YT105EDLA
files

| size  | name                                                                                        |
| ----- | ------------------------------------------------------------------------------------------- |
| 8gb   | `AP_X200XXS5DXJ5_X200XXS5DXJ5_MQB87759842_REV00_user_low_ship_MULTI_CERT_meta_OS14.tar.md5` |
| 10 Mb | `BL_X200XXS5DXJ5_X200XXS5DXJ5_MQB87759842_REV00_user_low_ship_MULTI_CERT.tar.md5`           |
### Prepare your Tablet 
(only necessary for first install on unrooted device)​

1. install USB drivers on PC
2. unlock OEM [[Samsung Tab A8 - OEM unlock]]
3. flash with [[Odin Downloader|Odin]] - [[Samsung Tab A8 - Start Bootloader]]
## access recovery menu
recovery menu
start tablet with volume up and power button held down

might error `[PDP] Back-up : fail setup-wizard [ FINISH ]`
## other
- [comment](https://stackoverflow.com/a/70178103) mentioning that Samsung devices have no fastboot
- [RECOVERY UNOFFICIAL TWRP 3.7.0 for 2021 Galaxy Tab A8 10.5 SM-X200](https://xdaforums.com/t/recovery-unofficial-twrp-3-7-0-for-2021-galaxy-tab-a8-10-5-sm-x200.4488691/)
- [[Samsung Tab A8 - Start recovery menu
