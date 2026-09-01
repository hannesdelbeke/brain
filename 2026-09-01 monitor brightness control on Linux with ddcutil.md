---
created: 2026-09-01
tags:
- technical
- linux
- fedora
- gnome
- display
aliases:
- monitor brightness control on Linux with ddcutil
- Monitorian equivalent on Linux
- ddcutil brightness control
---

How to control external and laptop monitor hardware brightness on Linux (Fedora / GNOME) using `ddcutil` and GNOME extensions, replacing Windows tools like [[public/Monitorian|Monitorian]].

Related: [[2026-08-29 new Linux PC setup log]], [[public/monitor|monitor]], [[public/Monitorian|Monitorian]]

## Problem
Default Linux desktop brightness sliders only interface with `/sys/class/backlight`, which controls internal laptop panels. External monitors require **DDC/CI** commands sent over the GPU I2C bus via `ddcutil`.

On Windows, [[public/Monitorian|Monitorian]] sits in the taskbar to provide quick popup sliders for all screens. On Linux GNOME, this requires `ddcutil` backend permissions plus a top-bar extension.

## Setup on Fedora

### 1. Install ddcutil and configure I2C permissions
Install the package, create the `i2c` group, and set up udev permissions so non-root desktop sessions can communicate with displays over `/dev/i2c-*`:

```bash
# 1. Install ddcutil
sudo dnf install -y ddcutil

# 2. Add user to i2c group
sudo groupadd --system i2c 2>/dev/null || true
sudo usermod -aG i2c $USER

# 3. Create udev rule granting read/write access to i2c devices
echo 'KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0666"' | sudo tee /etc/udev/rules.d/60-ddcutil-i2c.rules

# 4. Trigger udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 2. Verify display detection
Ensure DDC/CI is enabled in the monitor's physical On-Screen Display (OSD) settings, then test detection:

```bash
ddcutil detect
```

Example detected display:
```text
Display 1
   I2C bus:             /dev/i2c-17
   DRM_connector:       card1-DP-6
   EDID synopsis:
      Mfg id:           DEL - Dell Inc.
      Model:            AW2724DM
   VCP version:         2.1
```

Set brightness directly via CLI:
```bash
# Set Display 1 to 70% brightness
ddcutil setvcp 10 70
```

## Monitorian equivalent UI (GNOME top-bar icon)

Install the GNOME Shell extension **Brightness control using ddcutil** (via *Extension Manager* or extensions.gnome.org).

### Configuration for Monitorian workflow:
- In Extension Settings, set **Location** to `Top Bar / Panel`.
- Set **Show Icon** to `Always`.
- **Left click:** Opens flyout showing individual sliders for laptop screen and external monitors.
- **Scroll wheel:** Hovering mouse wheel over the top-bar icon adjusts brightness immediately without clicking.

## Latency & performance tuning

Hardware DDC/CI commands communicate over a 100 kHz I2C bus to the monitor's microcontroller, introducing a ~100–300ms hardware transaction latency compared to 0ms laptop GPU backlight changes.

To minimize delay in extension settings:
- **Skip verification (`--noverify`):** Eliminates the round-trip read confirmation after writing brightness values.
- **Lower sleep multiplier (`--sleep-multiplier 0.2` - `0.5`):** Speeds up inter-byte I2C pauses on modern monitor microcontrollers.
- **Bus caching:** Locks the display to its known I2C bus (e.g. `/dev/i2c-17`) to prevent scanning unused video ports on each slider tick.

## Keyboard shortcuts (20% step control)

Using keyboard hotkeys bypasses mouse dragging latency entirely, allowing instant step-based brightness changes across displays without opening menus.

### 1. Extension shortcuts
In the **Brightness control using ddcutil** extension settings:
- Set step increment size (e.g. **20%**).
- Bind global shortcuts to increase / decrease brightness across connected displays.

### 2. Native GNOME custom shortcuts
Alternatively, bind shortcuts under **Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts**:

```bash
# Increase external brightness by 20%
ddcutil setvcp 10 + 20 --noverify

# Decrease external brightness by 20%
ddcutil setvcp 10 - 20 --noverify
```
