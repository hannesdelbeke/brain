---
tags:
  - hardware
  - tech
  - review
origin-sha: 645baa21b
---
Comparison and used-market buying guide across ThinkPad X1 Yoga / 2-in-1 generations (Gen 7–11), Razer Blade 15, and Surface Pro 11.

## Generation Overview

- 🟢 **Gen 8 (2023, 13th Gen i7-1360P, 12c/28W):** The buy (£350–550 used). Garaged pen, 12-core CPU, identical solid chassis.
- 🟢 **Gen 7 (2022, 12th Gen i7-1270P/1280P):** Strong budget buy (£300–450 used). Same chassis, ports, and garaged pen as Gen 8.
- 🟡 **Gen 11 (2026, Panther Lake Ultra X7 368H, 16c):** Future buy (~2028). Redesigned bottom recess garaged pen, ~£1,900 new; wait for enterprise off-lease.
- 🟡 **Surface Pro 11 (Snapdragon ARM):** Wait for refresh (£970–1,230 used). Great battery, but x86 Docker emulation hurdles.
- 🔴 **Gen 9 (2024, Ultra 5/7 U-series, 15W):** Skip (~£1,050 used). Lost pen garage (magnetic side) and downgraded to 15W 2-core CPU.
- 🔴 **Gen 10 (2025, Lunar Lake Ultra 7 258V/268V):** Skip (£1,400+ used). Lost pen garage, expensive, and capped at 8 cores.

## Comparison with Razer Blade 15

Upgrading from the [[razor blade 15 rz09-02705w76 2018|Razer Blade 15]] (i7-8750H, GTX 1060 Max-Q, 2.07 kg) to a ThinkPad X1 Yoga (Gen 7/8) is a move from a heavy gaming laptop to a portable 1.38 kg 2-in-1 workstation:

- **Portability:** X1 Yoga is ~1.38 kg vs Razer's 2.07 kg (saving ~0.7 kg / 1.5 lbs in bag).
- **Form factor:** Adds 360° hinge, touchscreen, and built-in garaged stylus.
- **CPU compile speed:** 13th Gen i7-1360P (12 cores / 16 threads) is ~50%+ faster in multi-core compile benchmarks than the 2018 8th Gen i7-8750H (6 cores).
- **Graphics & thermals:** Razer retains dedicated GPU advantage for 3D gaming, while X1 Yoga offers far quieter fan acoustics, lower heat, and USB-C PD charging for coding.

## Gen 7 vs Gen 8 Comparison

- **Chassis & build:** Identical Storm Grey aluminum chassis, 360° hinge, ~1.38 kg weight.
- **Ports & features:** Dual Thunderbolt 4 ports, IR camera, fingerprint reader, built-in garaged pen.
- **Display options:** 16:10 aspect ratio ranging from 1200p IPS up to 4K OLED.
- **CPU difference:** Gen 8 (13th Gen) is a modest thermal and efficiency iteration over Gen 7 (12th Gen).

## Evaluation by Generation

**Gen 8 (Primary Pick)**
Last true "X1 Yoga" before Lenovo switched naming to "X1 2-in-1" and removed the built-in pen garage. 32GB models run £350–550 used.
🟢 **Verdict: The Buy.** Best balance of 13th Gen multi-core speed, garaged stylus, and used market value.

**Gen 7 (Budget Alternative)**
If priced at £300–400, it offers nearly identical daily performance and chassis build for less money.
🟢 **Verdict: Strong Buy on Discount.** Identical chassis and garaged pen if found under £400.

**Gen 11 (Future Target ~2028)**
16-core Panther Lake, under 1.2 kg, and restored garaged charging recess in the bottom panel. Target used around 2028 when enterprise lease cycles conclude.
🟡 **Verdict: Future Buy (~2028).** Outstanding hardware, but ~£1,900 new with no used market yet.

**Surface Pro 11 (Snapdragon ARM)**
32GB/1TB runs £970–1,230 used on Snapdragon ARM. Strong for text editing and web tasks, but x86 Docker containers still run under emulation.
🟡 **Verdict: Wait for Refresh.** ARM emulation trade-offs and X2 Elite refresh will push prices down.

**Gen 9 (Skip)**
Lenovo dropped the pen garage for a side magnetic pen and shifted to lower-power 15W U-series chips. A £1,050 Gen 9 compiles code slower than a £450 Gen 7.
🔴 **Verdict: Skip.** Slower 2-performance-core CPU and losable magnetic pen.

**Gen 10 (Skip)**
Efficient Lunar Lake chip, but thermally limited, capped at 8 cores, missing the pen garage, and £1,400+ used.
🔴 **Verdict: Skip.** Overpriced for an 8-core machine with no garaged pen.

## Acoustic & Thermal Reality: Which Laptops are Actually Dead Silent?

Real-world testing on the **ThinkPad X1 Yoga Gen 7 (i5-1245U)** showed it is **louder and warmer than expected**. Intel 12th Gen ("Alder Lake" 10nm) voltage spikes under light developer bursts (such as a single AI agent tool call or Python script) ramp package power to 35W+, triggering audible 3,000+ RPM fan noise rather than staying passive (0 RPM).

To achieve **dead silence (0 dB / 0 RPM) and cool-to-touch operation** during note-taking and AI sessions:

| Architecture / Laptop | Fan Acoustic Profile | Thermal Behavior | AI / Dev Fit |
| :--- | :--- | :--- | :--- |
| 🥇 **Apple MacBook Air (M2 / M3 / M4)** | **0.0 dB (100% Fanless)**. No fan exists. | Ice-cold / lukewarm (4–10W draw). | Unified memory runs local embeddings (`fastembed`) and Python/Node agents instantly with zero noise. (Trade-off: macOS, clamshell only). |
| 🥈 **Surface Pro 11 (Snapdragon X Plus/Elite)** | **Dead silent (0 RPM floor)** for light/medium loads. | TSMC 4nm ARM runs cool in hands (5–12W). | Best Windows 2-in-1 with touchscreen & Slim Pen 2; 45 TOPS NPU; 12–15h battery. |
| 🥉 **Lenovo Yoga Slim 7x (Snapdragon X Elite)** | **Virtually inaudible**. Fan off during AI turns. | Cool in lap; premium 1.28 kg OLED build. | Excellent Windows ARM ultraportable. |
| 💻 **ThinkPad T14s Gen 4/5 (AMD Ryzen 7840U/8840U)** | **Significantly quieter** than Intel 12th/13th Gen. | TSMC 4nm x86; low idle leakage. | Native x86 compatibility without ARM translation. |
| 💻 **Asus Zenbook S 14 / X1 Gen 10 (Intel Lunar Lake)** | **0 RPM idle/light load** (TSMC 3nm x86). | Fixes Alder Lake power leaks; idles <2W. | Premium price (£1,200+). |

## Bottom Line

- 🟢 **Purchased Budget Option:** ThinkPad X1 Yoga Gen 7 (£240 used) — functional 2-in-1 with garaged pen, but requires "Best Power Efficiency" mode to tame fan spin-ups.
- 🟢 **Top Fanless / Dead Silent Pick:** MacBook Air M2/M3 (16GB, £650–850 used) for 100% silent mobile coding.
- 🟢 **Top Silent Windows 2-in-1:** Surface Pro 11 (Snapdragon ARM) for silent tablet + pen workflows.
- 🟡 **Wait & Revisit:** Gen 11 (Panther Lake) around 2028 when off-lease prices drop.

### References
- [[Lenovo ThinkPad X1 Yoga Gen 7]] — specs and real-world acoustic review.
- [[GPU comparison - Razer Blade 15 vs ThinkPad X1 Yoga]] — comparison against gaming dGPU.
- [[public/linux dev likes quiet pc|linux dev likes quiet pc]] — why acoustic silence is critical for flow state.