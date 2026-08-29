---
created: 2026-08-29
origin-sha: bbe6b08e
tags:
- technical
- linux
- hardware
- fix
- krita
- thinkpad
aliases:
- Krita pen lag on Linux
- ThinkPad stylus latency fix
---

Investigating and resolving stylus / pen input lag in [[public/Krita|Krita]] on the [[public/Lenovo ThinkPad X1 Yoga Gen 7|Lenovo ThinkPad X1 Yoga Gen 7]] running Fedora [[public/Linux for AI and developer workflows|Linux]].

## Symptoms
- Active pen strokes trail visibly behind the stylus tip on the touchscreen.
- Drawing curves feels sluggish rather than instantaneous and responsive.
- Higher canvas resolutions (e.g. 300 DPI A4) amplify stuttering and input delay.

## Root Cause Analysis
1. **Brush Smoothing Delay Distance:** Krita defaulted to Weighted smoothing (`LineSmoothingType=1`) with a 50px delay distance (`LineSmoothingUseDelayDistance=true`). This intentionally buffers and lags stroke points to calculate curves, creating artificial input latency.
2. **Level of Detail (Instant Preview) Disabled:** `levelOfDetailEnabled=false` forced the Intel Iris Xe GPU to calculate and rasterize full-resolution pixel updates on every 200Hz digitizer event instead of rendering optimized downscaled canvas tiles in real-time.
3. **Widescreen Mirroring Aspect Ratio Mismatch (Coordinate Offset):**
   - ThinkPad physical screen & digitizer: **16:10 aspect ratio (1920x1200)**.
   - External monitor: **16:9 widescreen (1920x1080 / 2560x1440)**.
   - Duplicating displays forces a 16:9 resolution (`1920x1080`) across the 16:10 physical panel. Because `keep-aspect` was disabled, the Y-axis coordinates were squashed/stretched across the 1080p viewport, causing progressive vertical drift between the physical pen tip and the cursor.

## Applied Optimizations
- **Disabled Brush Smoothing Delay:** Set `LineSmoothingType=0` (None) for zero mathematical curve delay between digitizer points.
- **Matched 200 Hz Digitizer Polling Rate:** Configured `fpsLimit=200` and `disableVSync=true` in `kritadisplayrc` and `kritarc` to eliminate internal queue latency and match the Wacom AES hardware polling rate 1:1.
- **Enabled Instant Preview / Level of Detail:** Set `levelOfDetailEnabled=true` in `kritarc` for 60fps real-time stroke rasterization on Intel Iris Xe.
- **Multi-threaded Brush Engine:** Allocated 12 threads matching the Intel Core i5-1245U.
- **Fixed Digitizer Mapping & Aspect Ratio:**
  Locked the Wacom AES sensor (`056a:530a`) specifically to the built-in BOE panel with aspect-ratio preservation:
  ```bash
  gsettings set org.gnome.desktop.peripherals.tablet:/org/gnome/desktop/peripherals/tablets/056a:530a/ keep-aspect true
  gsettings set org.gnome.desktop.peripherals.tablet:/org/gnome/desktop/peripherals/tablets/056a:530a/ output "['BOE', '0x094c', '0x00000000']"
  gsettings set org.gnome.desktop.peripherals.tablet:/org/gnome/desktop/peripherals/tablets/056a:530a/ mapping 'absolute'
  ```

## Display Pipeline & Refresh Architecture
- **Active Inking:** The panel runs at locked **60.00 Hz** (1920x1200 native). Krita's 200 FPS internal tick ensures the newest pen coordinates are ready on the exact millisecond of every VSync interval.
- **Idle Power Savings (Intel PSR2):** When static, the Intel GPU enters Panel Self-Refresh sleep mode, letting the LCD buffer hold the image. Touching or hovering the stylus wakes the pipeline in `<1 ms`.
- **Display Mode for Drawing:** For 100% 1:1 hardware pixel-to-digitizer precision, run the laptop screen at native **1920x1200 (16:10)** (Extend or Single Display mode) rather than widescreen 16:9 duplicate.

## References
- [[public/Lenovo ThinkPad X1 Yoga Gen 7|Lenovo ThinkPad X1 Yoga Gen 7]] — hardware digitizer and touchscreen specifications
- [[public/Krita|Krita]] — open-source painting application
- [[public/Linux for AI and developer workflows|Linux for AI and developer workflows]] — Linux architecture
