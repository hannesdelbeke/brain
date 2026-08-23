---
tags:
  - technical
  - hardware
---
Real-world [[file transfer]] speeds for common interfaces. Theoretical max is rarely hit — protocol overhead, drive speed, and signal quality all eat into it.

## Wired

**[[thunderbolt 3 vs 4|Thunderbolt]] 3/4** — 40 Gbps theoretical, ~2–3 GB/s real. Fastest common option for direct device-to-device or external SSD. TB5 doubles to 80 Gbps (~5–6 GB/s). Bottleneck is usually the SSD, not the bus.

**USB 3.2 Gen 2** — 10 Gbps theoretical, ~800–1000 MB/s real. Most external drives ship with this. Gen 2x2 (20 Gbps) exists but rare. USB 3.0 (Gen 1) caps at 5 Gbps, ~350–400 MB/s real.

**Ethernet (1 GbE)** — 1 Gbps theoretical, ~110 MB/s real. Standard on most desktops and docks. Fine for documents, painful for large media. 2.5 GbE (~280 MB/s) is becoming common on newer hardware. 10 GbE (~1.1 GB/s) rivals USB 3.2 but needs compatible switches and NICs.

## Wireless

**WiFi 6 (ax)** — 1.2–2.4 Gbps theoretical on 5 GHz, ~100–200 MB/s real depending on range and interference. WiFi 6E/7 push theoretical higher but real-world gains depend heavily on environment. Never as reliable as wired for sustained transfers.

**WiFi 5 (ac)** — ~50–100 MB/s real in good conditions. Drops fast through walls.

## Practical takeaway

For moving a 100 GB folder:

- Thunderbolt 4: ~40–50s
- USB 3.2 Gen 2: ~1.5–2 min
- 2.5 GbE: ~6 min
- 1 GbE: ~15 min
- WiFi 6 (good signal): ~8–15 min
- WiFi 5: ~15–30 min

If you have Thunderbolt on both ends, use it. If not, USB 3.2 Gen 2 with a decent SSD is the next best. Network transfers (Ethernet/WiFi) add SMB/NFS protocol overhead on top of the link speed.
