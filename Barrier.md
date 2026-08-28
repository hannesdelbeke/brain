---
sentiment:
- 5
sentiment-hash: 00a43955
sentiment-label:
- factual
tags:
- technical
- software
- tools
aliases:
- Barrier Ethernet setup
- Barrier WiFi lag
---

# Barrier

Barrier is an open-source [[virtual]] [[keyboard video mouse|KVM]] software to control multiple computers seamlessly using 1 [[computer mouse|mouse]] and 1 [[keyboard]].

Moving the cursor past the edge of one monitor transitions focus directly to the adjacent computer's screen over local network, functioning like a multi-monitor desktop across distinct physical machines.

*KVM stands for "keyboard, video, mouse."*

> [!winget install]- 
> install with [[winget]]
> ```batch
> winget install DebaucheeOpenSourceGroup.Barrier
> ```

---

## 🌐 Network Setup: Eliminating WiFi Lag via Dedicated LAN

Using Barrier over standard [[WiFi]] can introduce periodic jitter, packet drop, or cursor input lag.

### Low-Latency Wired Configuration
1. Connect all computers directly to a dedicated gigabit [[network switch]] using [[Ethernet]] cables.
2. Assign a [[static IP address]] to the Ethernet adapter on the Barrier server PC (e.g. `192.168.1.100`).
3. Point Barrier clients to the server's static LAN IP. This ensures clients reliably reconnect over high-speed Ethernet after a reboot without falling back to WiFi.

---

## 🛠️ Troubleshooting & Known Workarounds

### 1. SSL Certificate Missing (`ERROR: ssl certificate doesn't exist`)
Regenerate the SSL certificate manually via OpenSSL:
```powershell
Set-Alias openssl "C:\Program Files\Git\usr\bin\openssl.exe"
cd ~\AppData\Local\Barrier\SSL\
openssl req -x509 -nodes -days 365 -subj /CN=Barrier -newkey rsa:4096 -keyout Barrier.pem -out Barrier.pem
```
*(Reference: [GitHub Issue #231](https://github.com/debauchee/barrier/issues/231#issuecomment-1143791895))*

### 2. "Failed to start server" on Launch
Downgrade temporarily to initialize configuration, then upgrade:
```powershell
winget uninstall barrier
winget install barrier --version 2.3.3-release
# Run Barrier once to initialize config files, then exit and upgrade:
winget upgrade barrier
```

### 3. VPN Compatibility
Barrier packets are often blocked if a client/server is routed through a full-tunnel [[virtual private network|VPN]].
* **Workaround:** Establish the local Barrier connection *before* launching the VPN client.

### 4. Service Halts on UAC / Admin Prompts
1. Open Barrier **Settings**.
2. Change the **Elevate** option from `as needed` (default) to **`always`**.

### 5. Cursor Trapped in Screen Corner (High DPI Scaling Bug)
When Windows display scaling on the Server or Client is set above 100% (e.g. 125% or 150%), Barrier's virtual coordinate calculation can fail, trapping the cursor in the bottom corner.
* **Fix A:** Set Server Windows display scaling to **100%** (Settings > Display > Scale: 100%).
* **Fix B:** Right-click `barrier.exe` (and `barrierc.exe` / `barriers.exe`) > **Properties** > **Compatibility** > **Change high DPI settings** > Check **"Override high DPI scaling behavior"** > Set to **"Application"**.

---

> [!NOTE] Forensic Provenance
> Consolidated on 2026-08-28 from exploratory stubs `Barrier WiFi lag.md` and `Barrier Ethernet setup.md`. To inspect raw previous iterations, use `git log -S "Barrier WiFi lag" -p` or `git log -S "Barrier Ethernet setup" -p`.

[[virtual solution]]