---
tags:
  - hardware
  - homelab
  - nas
---
> find top value deal for laptop with broke nscreen but still functional. to use as a NAS or homeserver. old small pc is also an option

second hand hardware for an always-on file server, comparing a cracked-screen business laptop against an ex-corporate 1 litre mini pc. uk market, prices are eBay sold-listing ballparks rather than quotes, since eBay blocks automated fetching and the numbers move.

## verdict

the mini pc wins unless the laptop is close to free.

a laptop with a dead display is cheap because the repair costs more than the owner thinks the machine is worth, and the [usual homelab advice](https://www.howtogeek.com/repurpose-laptop-with-broken-screen/) treats the missing screen as a bonus for power draw. the catch is everything else about a laptop is wrong for a box that never turns off:

- the battery is the problem, not the feature. a five year old cell run at permanent float charge is a swelling risk, and the free ups argument only holds while the cells are healthy.
- one drive bay, and the second drive has to hang off usb.
- lid close and sleep behaviour needs configuring before it will stay up, and wake after power loss is not always exposed in the firmware.

the mini pc form factor is designed for the opposite. a [thinkcentre tiny](https://www.ebay.co.uk/shop/m720q?_nkw=m720q), optiplex micro or elitedesk mini takes a 2.5" sata drive and an m.2 nvme at the same time, ships with power on after ac loss in the bios as a standard corporate feature, and the lenovo tiny models have a pcie riser slot that will take a 2.5gbe or 10gbe sfp+ card later. supply is high because these come off corporate refresh cycles in bulk, which is what keeps the price down.

## what to buy

the sweet spot is an 8th gen i5 with a t suffix, so i5-8400t or i5-8500t, with 8 to 16gb ddr4, at roughly £60 to £110 including the power supply.

- lenovo thinkcentre m720q or m920q tiny, pick this one if the pcie riser matters
- dell optiplex 3060 or 5060 micro
- hp elitedesk 800 g4 mini

the t suffix is a 35w part and idles somewhere around 8 to 12w. the uhd 630 graphics give quick sync, which is what [jellyfin](https://jellyfin.org/) or plex need for hardware transcoding.

going up a generation to 11th gen or newer, so an m70q gen 2 or optiplex 3090 micro at £130 to £180, buys newer hevc and av1 decode. only worth it if the media library needs it.

avoid anything pre 8th gen, 4gb of ram, hdd only, or listed without a power supply. the barrel psu on these is model specific and about £15 to replace.

when searching, filter to sold items and uk only. search engine snapshots of eBay pages do not carry live prices. [bargain hardware](https://www.bargainhardware.co.uk/refurbished-desktop-pcs/dell-optiplex/dell-micro-usdt) and [dell refurbished uk](https://www.dellrefurbished.co.uk/category/store-dt-ultra/desktops/micro/1.html) give a warranty backed baseline to compare an auction against.

## if it is a laptop anyway

target a latitude 7490, thinkpad t480 or elitebook 840 g5 with a cracked display, around £40 to £70. the [latitude 7400 class machine](https://www.howtogeek.com/a-broken-laptop-is-the-best-nas-host-device-you-can-buy/) is the one that keeps coming up as the value pick.

read the listing carefully. sellers who list as spares or repair often strip the ram, the ssd and the drive caddy before shipping, and the charger is frequently missing. ask before bidding.

once it arrives, pull the battery out entirely and run it on mains. the ups benefit is not worth a swelling cell in a cupboard.

## storage

both options top out at two internal drives, so bulk capacity lives in a powered usb 3 enclosure with 3.5" drives. bus powered 2.5" enclosures brown out under sustained write.

neither of these should hold the only copy of anything. the truenas community position on laptops as a host is that they belong in a test bed, and the same reasoning applies to a single mini pc with no redundancy.

## related

[[2025-12-02 laptop research]]
