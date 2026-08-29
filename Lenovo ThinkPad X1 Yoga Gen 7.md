---
aliases:
  - ThinkPad X1 Yoga Gen 7
  - ThinkPad X1 Yoga
tags:
  - hardware
  - review
  - setup
origin-sha: c89b45c8
created: 2026-08-26
---

The **ThinkPad X1 Yoga Gen 7** is a 2-in-1 convertible [[laptop]] with touchscreen and pen support.
## Specs
- **Model:** Lenovo ThinkPad X1 Yoga Gen 7 (`21CES06A00`)
- **CPU:** 12th Gen Intel Core i5-1245U (10 cores / 12 threads, up to 4.40 GHz)
- **RAM:** 16 GB LPDDR5
- **Storage:** 256 GB NVMe SSD (`SKHynix_HFS256GDE9X081N`)
- **Display:** 14" WUXGA (1920x1200) IPS Touchscreen (FlexView, Stylus / Active Pen)
- **Graphics:** Intel Iris Xe Graphics
- **Battery:** 57 Wh design capacity (current health: ~40.5 Wh, 194 cycles, 80% charge threshold set in EC firmware)
- **OS:** Dual-boot [[Fedora]] Workstation 44 & [[Windows 11]] Pro

## AI & Hardware Acceleration
- **No Dedicated NPU:** 12th Gen Alder Lake lacks dedicated NPU silicon (introduced in 14th Gen Intel Core Ultra) and discrete GPU VRAM, making LLM throughput bound by ~45 GB/s LPDDR5 system bandwidth.
- **Intel DL Boost (AVX-VNNI):** Hardware vector instructions on CPU accelerating INT4 / INT8 quantized integer math. Enables 3B models (`llama3.2:3b`, `qwen2.5:3b`) to run at **25–35 tok/sec** locally.
- **Intel Iris Xe iGPU:** 80 Execution Units supporting OpenVINO, Vulkan, and OpenCL for offloading embeddings and matrix multiplication.
- **Intel GNA 3.0:** Ultra-low-power neural coprocessor dedicated to microphone noise cancellation.

## Notes & Review
- **Acoustics & Thermals:** Louder and warmer than expected. It is tolerable, but **not dead silent** when doing basic tasks like running an AI session or compiling metadata.
- **Fan Behavior:** Rather than remaining passive (0 RPM) during sustained light work, the Intel 12th Gen i5-1245U spins up the fans noticeably under light burst loads.
- **Form Factor & Daily Use:** Good overall 2-in-1 convertible build, solid touchscreen, and light portability compared to the Razer Blade 15.

## References
- [[local LLM generation speed vs human reading speed]] — local 3B vs 7B generation throughput on this laptop
- [[2026-08-29 new Linux PC setup log]] — Fedora installation and developer setup log
- [[2026-08-29 installing Fedora on the Yoga without working USB ports]] — internal NVMe boot installer procedure
- [[2026-08-29 Krita pen lag and stylus latency on Linux|Krita pen lag on Linux]] — Wacom AES stylus latency calibration
- [[GPU comparison - Razer Blade 15 vs ThinkPad X1 Yoga]] — architecture and local AI comparison against Razer Blade 15
- [[2026-08-11 laptop research]] — purchasing evaluation for ThinkPad X1 Yoga generations
- [eBay listing](https://www.ebay.co.uk/itm/336700456020) 240£
