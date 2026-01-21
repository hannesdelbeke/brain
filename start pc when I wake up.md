To start my pc on wake up with [[Home Assistant]]

TRIGGER options
- trigger with phone motion, when I wake up. I don't see a sensor for this
- motion sensor in room

IF
- presence check - only trigger if you’re home.
- ensure pc is not on / drawing power
- Add a time window, weekdays between 7am and 10am

THEN
- toggle power smart socket
	- this triggers start since in bios set to power on after power loss

Prevent multiple triggers in the same morning.