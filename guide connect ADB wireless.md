---
views: 1
---
To make scrcpy work over your network, you need to manually connect adb to your phone's wireless debugging port.
Follow these steps:

### Step 1: Find the IP Address and Port

1. On your Android phone, go to Settings > Developer options > Wireless debugging.
2. Make sure Wireless debugging is turned ON.
3. Under IP address & Port, look at the values listed (e.g., 192.168.1.15:39847).
(Note: The port number changes every time you turn Wireless debugging off/on or reboot).

### Step 2: Pair the PC and Phone (First-time setup only)

4. On your phone, tap Pair device with pairing code. You will see:
• A pairing Wi-Fi pairing code (6 digits).
• An IP address & Port (e.g., 192.168.1.15:43217 — this pairing port is different from the connection port in
Step 1).
5. Open PowerShell or Command Prompt on your PC and run:
`adb pair <IP>:<PAIRING_PORT>`
Example: `adb pair 192.168.1.15:43217`
6. Enter the 6-digit pairing code when prompted.

### Step 3: Connect ADB to the Phone

7. Go back to the main Wireless debugging screen on your phone.
8. Note the main IP address & Port (from Step 1).
9. On your PC, run:
`adb connect <IP>:<PORT>`
Example: `adb connect 192.168.1.15:39847`
10. It should output: connected to 192.168.1.15:39847.

### Step 4: Run scrcpy

Now you can start mirroring:

scrcpy --video-bit-rate 2M --max-size 800

### Troubleshooting Network Issues

If the adb pair or adb connect commands fail to connect/timeout:

• AP / Client Isolation: Check your router settings to ensure AP Isolation (sometimes called Client Isolation or
WLAN Partition) is disabled. If enabled, it blocks wireless devices (your phone) from communicating with wired
devices (your PC) even on the same router.
• Firewall: Make sure your PC's network profile is set to Private and Windows Defender Firewall is not blocking adb.
exe or scrcpy.exe.

