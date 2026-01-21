
- go to bios, search for `Power On By PCI-E` and enable it.
- disable `ErP` in bios. already disabled
- `Control Panel\Hardware and Sound\Power Options\System Settings`
	- choose what power button does
	- disable `turn on fast startup` - greyed out & already disabled

doesn't seem to work,

1. check if we are in the correct sleep state
```powershell
powercfg /a
```
if it says `Standby (S0 Low Power Idle)` instead of `S3`, then your device uses S0 low power idle, which doesn't support WoL. Mine does support it

2. print devices that support Wake on LAN, ensuring our network adapter is listed. It is
```powershell
powercfg -devicequery wake_from_any
```

3. print drivers
```powershell
Get-NetAdapter | Format-Table Name, InterfaceDescription, DriverVersion, DriverProvider
```

```
Name                         InterfaceDescription                                DriverVersion   DriverProvider
----                         --------------------                                -------------   --------------
Bluetooth Network Connection Bluetooth Device (Personal Area Network)            10.0.26100.5074 Microsoft
vEthernet (Default Switch)   Hyper-V Virtual Ethernet Adapter
Ethernet 2                   Intel(R) Ethernet Converged Network Adapter X540-T2 4.1.228.0       Intel
Ethernet 4                   PANGP Virtual Ethernet Adapter Secure #2            16.15.20.869    PaloAltoNetworks
Local Area Connection        Intel(R) X722 Multi-Function Network Device         4.1.228.0       Intel
Ethernet                     Realtek PCIe 2.5GbE Family Controller               1.0.0.14        Microsoft
vEthernet (external)         Hyper-V Virtual Ethernet Adapter #2                 10.0.26100.1    Microsoft
Wi-Fi                        Intel(R) Wi-Fi 6 AX201 160MHz                       22.250.1.2      Intel
```

using the **Microsoft inbox driver**, not the Realtek OEM driver. Doesn't expose WoL

[[get motherboard model on Windows]]
restart pc

in device manager we can see

| Network Adapter                                     | WOL Support                                |
| --------------------------------------------------- | ------------------------------------------ |
| Bluetooth Device (Personal Area Network)            | has WOL                                    |
| Hyper‑V Virtual Ethernet Adapter #2                 | doesn't even have WOL tab                  |
| Intel(R) Ethernet Converged Network Adapter X540‑T2 | no WOL, greyed out                         |
| Intel(R) Wi‑Fi 6 AX201 160MHz                       | has WOL                                    |
| Intel(R) X722 Multi‑Function Network Device         | doesn't even have WOL tab                  |
| PANGP Virtual Ethernet Adapter Secure #2            | doesn't even have WOL tab                  |
| Realtek Gaming 2.5GbE Family Controller             | has WOL, shows up in BIOS with MAC address |
turns out I was looking at wrong one (Intel(R) Ethernet) but `Realtek Gaming 2.5GbE Family Controller` is the one I need.

[[Windows - get mac addresses ]]
Confirm the NIC is actually armed for wake

```powershell
powercfg -devicequery wake_armed
```

> [!output]-
> ```
> HID Keyboard Device
> HID-compliant mouse
> Realtek Gaming 2.5GbE Family Controller
> Intel(R) Wi-Fi 6 AX201 160MHz
> HID Keyboard Device (001)
> HID Keyboard Device (002)
> HID-compliant mouse (002)
> ```

check if WoL is setup
```powershell
Get-NetAdapterAdvancedProperty -Name "Ethernet" | Where-Object {$_.DisplayName -like "*Wake*"}
```

> [!output]-
> ```
> Name                      DisplayName                    DisplayValue                   RegistryKeyword RegistryValue
> ----                      -----------                    ------------                   --------------- -------------
> Ethernet                  Wake on Magic Packet           Enabled                        *WakeOnMagic... {1}
> Ethernet                  Wake on pattern match          Enabled                        *WakeOnPattern  {1}
> Ethernet                  Shutdown Wake-On-Lan           Enabled                        S5WakeOnLan     {1}
> ```
> 

The ethernet light goes off when sleep pc

**Disable ASUS Fast Boot (BIOS)**
Boot → Boot Configuration → Fast Boot  → `Disabled`

ethernet light still powers off.

Let's double check: 

Advanced/APM configuration
- ErP Ready is disabled
- Max power savings is disabled
- power on by pci-e is enabled

these were enabled,Ii disabled them
- PCI Express Native Power Management - set to Disabled
- ASPM - set to Disabled

these already were disabled 
- L1 Substates → Disabled
- DMI ASPM → Disabled
- PEG ASPM → Disabled

Advanced → Onboard Devices Configuration
- Realtek LAN Controller → Enabled

After wasting over 3h yesterday, I give up on [[Wake on LAN]].
And instead set restore power -> power on
and start the pc with a smart socket from [[Home Assistant]].