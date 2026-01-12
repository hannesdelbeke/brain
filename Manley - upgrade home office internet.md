my modern work pc gets [[wifi]] speeds of 500mb/s
my old [[razor blade 15 rz09-02705w76 2018|personal laptop]] is only 70mb/s
the dongle on the [[HAOS]] server is only 30mbps (ancient dongle)
and my desktop with a pci-e wifi card gets 150mbps.
## wireless bridge
I could consider ethernet, but 500mbps is fast, a wifi bridge might be better than [[Powerline Ethernet Adapter]], I was looking at MIMO wifi extenders.

you can use wifi extenders in 2 ways
- Repeater Mode (which slows things down) 
- Bridge Mode (aka Client Mode) (which doesn't).

AI suggested Wi‑Fi 6 or 6E extender in Client/Bridge Mode:
- TP‑Link RE605X
- ASUS RP‑AX58
- Netgear EX6250 / EX6400
- Any Wi‑Fi 6/6E extender with “Media Bridge” or “Client Mode”

I [[setup TP-LINK RE605X Ax1800]], disabled Wi-Fi on my pc-s and speed went up to 500mbps on all [[network switch]] connected devices. A big improvement.
## share internet
Turns out i can also share internet speed from my work pc to my personal laptop over Ethernet, through the [[network switch]] i already have setup for [[Barrier]].
- changed my personal ethernet ip from static to automatic
- on [[work pc]]: change adapter settings /  right click on wifi. click properties -> sharing tab/ allow others to connect
- or under advanced network settings/wifi/more adapter options / sharing tab 

Since I didn't want to use work hardware for personal use, keep my personal network private, and avoid VPN issues, I went with the wireless bridge. It works well.