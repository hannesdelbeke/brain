---
sentiment:
- 5
sentiment-hash: c48ed065
sentiment-label:
- factual
tags:
- technical
- home
---
a better version of [[Wi-Fi extender]]. historically compared to [[Powerline Ethernet Adapter|Powerline]], but modern Wi-Fi 6/7 mesh significantly outperforms Powerline in both throughput and latency.

combining Wi-Fi mesh/bridge and Powerline does not produce "best of both worlds":
- creates a layer 2 network loop (broadcast storm) unless running managed STP
- bonding different-speed links causes out-of-order packet delivery and TCP throughput collapse
- hybrid mesh backhauls switch paths erratically under electrical noise, introducing jitter
