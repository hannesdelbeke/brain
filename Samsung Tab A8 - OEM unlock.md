
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
