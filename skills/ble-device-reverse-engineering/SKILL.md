---
name: ble-device-reverse-engineering
description: Standard operating procedure and Python tooling to scan, inspect, reverse-engineer, and automate Bluetooth Low Energy (BLE) IoT hardware (smart blinds, sensors, and controllers).
aliases:
  - ble device reverse engineering
  - ble-device-reverse-engineering
  - ble iot control
created: 2026-08-26
tags:
  - technical
  - hardware
  - bluetooth
  - smart-home
  - skill
---

# BLE Device Reverse-Engineering & Automation Skill

A comprehensive standard operating procedure (SOP) and Python toolset for discovering, enumerating, reverse-engineering, and automating Bluetooth Low Energy (BLE) IoT hardware (smart blinds, motors, relays, and home automation peripherals).

---

## 🎯 When to Use This Skill
Activate this skill when an agent or developer needs to:
1. Discover unknown or white-label Bluetooth Low Energy devices in the local environment.
2. Enumerate GATT Services and Characteristics (`read`, `write`, `notify`, `indicate`).
3. Reverse-engineer proprietary binary/hex command structures (e.g. Tuiss SmartView, Hunter Douglas, Tuya BLE, Dooya).
4. Automate local device control from Python without cloud vendor lock-in.

---

## 🔒 Privacy & Data Boundary Rules

When documenting or publishing IoT hardware reverse-engineering findings:

| Data Type | Example | Classification | Handling Rule |
| :--- | :--- | :---: | :--- |
| **Physical MAC Address** | `E4:96:89:XX:XX:XX` | 🔒 **PRIVATE** | **Never commit to public repos.** MAC addresses uniquely identify physical hardware. Accept via CLI flag (`--mac`) or environment variables. |
| **Physical Dimensions** | `1840mm x 1385mm` | 🔒 **PRIVATE** | Identifies specific window/room architectural details. Keep in private notes. |
| **GATT Service & Char UUIDs** | `0000fe50-0000-1000-8000-00805f9b34fb` *(example)* | 🌐 **PUBLIC** | Firmware constants shared across all units of that model. Safe to publish. Substitute real UUIDs from `inspect_ble.py` output. |
| **Command Hex Sequences** | `ff78ea41bf030000` | 🌐 **PUBLIC** | Generic motor protocol format; contains zero credentials or tokens. Safe to publish. |
| **Automation Scripts** | `tuiss_blind_controller.py` | 🌐 **PUBLIC** | Code logic is generic and sanitized. Safe to publish. |

## 📂 Files & Scripts in this Skill

- `SKILL.md` — this skill specification, standard operating procedure, and privacy rules.
- [[scan_ble.py]] — fast, passive BLE discovery scanner with RSSI, local name, service UUIDs, and manufacturer data.
- [[inspect_ble.py]] — GATT service and characteristic inspector for discovering write/notify channels.
- [[tuiss_blind_controller.py]] — parameterized CLI controller for Tuiss SmartView / Hunter Douglas BLE motorized blinds (`open`, `close`, `stop`, `position 0-100`).

---

## 🛠️ Step-by-Step Agent SOP

### Step 1: Scan Nearby BLE Devices ([[scan_ble.py]])
Use passive BLE advertisement scanning to identify candidate MAC addresses and advertised local names:

```bash
python skills/ble-device-reverse-engineering/scan_ble.py --timeout 8
```

### Step 2: Enumerate GATT Characteristics ([[inspect_ble.py]])
Connect to the device to discover its read, write, and notify channels:

```bash
python skills/ble-device-reverse-engineering/inspect_ble.py <TARGET_MAC>
```
Look for:
- **Write Characteristic:** Property `write` or `write-without-response` (the input command pipe).
- **Notify / Indicate Characteristic:** Property `notify` or `indicate` (the feedback status pipe).

### Step 3: Handle the "Single BLE Connection Lock" Rule
> [!IMPORTANT]
> Battery-powered BLE peripherals (blinds, smart locks, sensors) **only support 1 active GATT connection at a time**.
> If your script holds the connection open, mobile apps and Home Assistant will be locked out.
> **Rule:** Connect ➔ Transmit command ➔ Await acknowledgment ➔ **Immediately disconnect**.

### Step 4: Protocol Decoding Hierarchy
1. **GitHub Open Source Search:** Search for `"<Vendor Name>" OR "<Motor Model>" BLE bleak` (e.g. [pink88/Tuiss2HA](https://github.com/pink88/Tuiss2HA)).
2. **Android APK Decompilation:** Decompile the vendor's APK using `jadx` to extract packet formatting methods and encryption keys.
3. **Android Bluetooth HCI Snoop Log:** Enable HCI snoop log in Android Developer Options, perform actions in the official app, and inspect `btsnoop_hci.log` in Wireshark.

---

## 🪟 Case Study: Tuiss SmartView / Hunter Douglas Motor Protocol

The protocol used by Tuiss SmartView (e.g. TS5300 / TS5200 motors) uses structured hex frames:

### 1. Connection Handshake
Must be sent immediately upon connection to prevent the motor from terminating the link:
```
ff03030303787878787878
```

### 2. Dynamic Timestamp Sync
Synchronizes the motor's internal real-time clock for local schedules:
```
ff78ea41 + {YY}{MM}{DD}{HH}{MM}{SS}
Example (2026-08-26 23:15:36): ff78ea411a081a171536
```

### 3. Position Calculation Formula
The position command uses an inverted percentage scaled to 0–1000 travel steps:
```python
tuiss_percent = 100 - user_percent
total_val = int(round(tuiss_percent * 10))  # 0 (Open) to 1000 (Closed)
pos_low = total_val % 256
pos_high = total_val // 256
command_hex = f"ff78ea41bf03{pos_low:02x}{pos_high:02x}"
```

- **Fully Open (100%):** `ff78ea41bf030000`
- **Halfway (50%):** `ff78ea41bf03f401`
- **Fully Closed (0%):** `ff78ea41bf03e803`
- **Emergency Stop:** `ff78ea415f0301`

---

## 🚀 Running the Included Tools

### 1. Scan for Nearby Devices ([[scan_ble.py]])
```bash
python skills/ble-device-reverse-engineering/scan_ble.py
```

### 2. Inspect GATT Services of Any Device ([[inspect_ble.py]])
```bash
python skills/ble-device-reverse-engineering/inspect_ble.py <MAC_ADDRESS>
```

### 3. Control a Tuiss SmartView Blind ([[tuiss_blind_controller.py]])
```bash
# Pass MAC via CLI:
python skills/ble-device-reverse-engineering/tuiss_blind_controller.py --mac <MAC_ADDRESS> --action open
python skills/ble-device-reverse-engineering/tuiss_blind_controller.py --mac <MAC_ADDRESS> --position 50
python skills/ble-device-reverse-engineering/tuiss_blind_controller.py --mac <MAC_ADDRESS> --action close

# Or set environment variable:
export TUISS_BLIND_MAC="XX:XX:XX:XX:XX:XX"
python skills/ble-device-reverse-engineering/tuiss_blind_controller.py --action open
```

---

## 🔗 References
- [Bleak Python BLE Library](https://github.com/hbldh/bleak)
- [Tuiss2HA Home Assistant Component](https://github.com/pink88/Tuiss2HA)
- [Android Bluetooth HCI Snoop Log Guide](https://source.android.com/docs/core/connect/bluetooth/verifying_debugging#debugging-with-logs)
