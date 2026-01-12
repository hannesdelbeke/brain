Set upp my extender, to receive [[WiFi]], and forward it over [[ethernet]] to my pc-s.

- [[Wi-fi Protected Setup|WPS]] didnt work untill i reset the extender, with the small reset button
- pair with WPS
- get settings to access dashboard
	- install TP-Link Tether [[Android app]]
	- log in 
- no need to config settings, just had to wait a few min for [[ethernet]] to connect

some sites now don't load e.g. www.ebay.co.uk
AI tells me to try IP to rule out DNS issues [199.59.148.82](199.59.148.82), still unreachable.
Try lower MTU, still doesn't work

Turns out it was because my windows set a static IP for the ethernet, and used a google DNS, changing it back to obtain automatic fixed it. This was a leftover from [[Barrier Ethernet setup]]
### dashboard
should be able to access dashboard from http://tplinkrepeater.net/ when
- connected to wifi extender over wifi.
- connected over ethernet, and the extender has the same wifi network name as the main wifi (works now)
- connect to the extender LAN ip. current 192.168.1.64
