---
tags:
  - technical
  - hardware
---
Real-world [[file transfer]] speeds for common interfaces. Theoretical max is rarely hit — protocol overhead, drive speed, and signal quality all eat into it.

in order of fastest
- Thunderbolt 4
- ethernet 10 GbE / fiber
- USB 3.2 Gen 2
- ethernet 5 GbE
- WiFi 7 (close range)
- ethernet 2.5 GbE
- ethernet 1 GbE
- WiFi 6

## Wired

**[[thunderbolt 3 vs 4|Thunderbolt]] 3/4** — 40 Gbps theoretical, ~2–3 GB/s real. Fastest common option for direct device-to-device or external SSD. TB5 doubles to 80 Gbps (~5–6 GB/s). Bottleneck is usually the SSD, not the bus.

**USB 3.2 Gen 2** — 10 Gbps theoretical, ~800–1000 MB/s real. Most external drives ship with this. Gen 2x2 (20 Gbps) exists but rare. USB 3.0 (Gen 1) caps at 5 Gbps, ~350–400 MB/s real.

**Ethernet** — common tiers for local file transfer:
- **1 GbE** — ~110 MB/s real. Standard on most desktops and docks. Fine for documents, painful for large media.
- **2.5 GbE** — ~280 MB/s real. Becoming standard on newer motherboards and laptops. Good middle ground.
- **5 GbE** — ~550 MB/s real. Less common, mostly NAS and prosumer gear.
- **10 GbE** — ~1.1 GB/s real. Rivals USB 3.2 Gen 2. Needs compatible switches and NICs — Cat6a cable minimum, or SFP+ fiber.

**Fiber (SFP+/SFP28)** — 10/25 GbE over fiber optic, same speeds as copper Ethernet but over longer runs without signal degradation. 25 GbE (~2.5 GB/s) approaches Thunderbolt territory. Mostly datacenter and home lab — needs fiber NICs and a compatible switch.

Note: ISP "fiber" (FTTH) refers to your internet uplink speed (typically 1–10 Gbps), which limits internet transfers but not local LAN transfers between your own devices.

## Wireless

**WiFi 7 (be)** — 46 Gbps theoretical, ~3–5 Gbps real at close range (~375–625 MB/s). Multi-Link Operation (MLO) bonds 2.4/5/6 GHz bands simultaneously for better stability. 320 MHz channels double WiFi 6E's width. Degrades fast through walls — at range expect closer to WiFi 6 speeds. Needs WiFi 7 on both router and client.

WiFi 7 at close range beats 1 GbE and 2.5 GbE, roughly matches 5 GbE, but still loses to 10 GbE. The difference: Ethernet is consistent. WiFi 7 fluctuates with distance, walls, interference, and how many devices share the network.

**WiFi 6 (ax)** — 1.2–2.4 Gbps theoretical on 5 GHz, ~100–200 MB/s real depending on range and interference. Never as reliable as wired for sustained transfers.

**WiFi 5 (ac)** — ~50–100 MB/s real in good conditions. Drops fast through walls.

## Practical takeaway

For moving a 100 GB folder:

- Thunderbolt 4: ~40–50s
- 10 GbE: ~1.5 min
- USB 3.2 Gen 2: ~1.5–2 min
- 5 GbE: ~3 min
- WiFi 7 (close range): ~2.5–4.5 min
- 2.5 GbE: ~6 min
- 1 GbE: ~15 min
- WiFi 6 (good signal): ~8–15 min
- WiFi 5: ~15–30 min

If you have Thunderbolt on both ends, use it. If not, USB 3.2 Gen 2 with a decent SSD is the next best for direct transfers. For network transfers, 10 GbE is the speed king but needs infrastructure. WiFi 7 is surprisingly competitive with mid-tier Ethernet at close range, but Ethernet wins on consistency — no walls, no interference, no negotiation.
