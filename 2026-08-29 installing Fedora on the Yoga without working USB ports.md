---
tags:
- linux
- fedora
- thinkpad
- hardware
- dual-boot
aliases:
- installing fedora on the yoga without a working usb port
- installing linux without usb
- usb-less fedora live install
---

How to install Fedora Workstation alongside Windows from an internal NVMe partition when laptop USB ports disconnect during boot.

## The constraint

The [[Lenovo ThinkPad X1 Yoga Gen 7]] had a hardware fault where USB controllers disconnected roughly three minutes after boot. This made standard USB installer tools like Fedora Media Writer or Ventoy fail mid-boot.

The solution was to place the live installer on a dedicated internal NVMe partition and boot it directly through rEFInd at the EFI fallback path.

## Setup

1. **Partitioning:** In Windows, created a 7 GB FAT32 partition labelled `FEDORA` on Disk 0.
2. **Payload:** Robocopied the contents of the Fedora Workstation Live ISO directly onto the `FEDORA` partition.

## Boot configuration issues & fixes

- **Windows Boot Manager cannot chainload GRUB:** A `bcdedit` entry under `{bootmgr}` pointing at `\EFI\BOOT\BOOTX64.EFI` appears in the blue Windows OS menu but fails when selected (bootmgr only loads Windows osloaders). Firmware entries must live in NVRAM under `{fwbootmgr}`.
- **Wrong GRUB config:** `E:\boot\grub2\grub.cfg` is for legacy BIOS only. The UEFI config is `E:\EFI\BOOT\grub.cfg`. In `grub.cfg`, replaced `CDLABEL=Fedora-WS-Live-*` with `LABEL=FEDORA` in the `root=live:` and `inst.stage2=hd:` arguments to avoid a dracut emergency shell.
- **Secure Boot & rEFInd:** rEFInd is unsigned, so UEFI firmware silently rejected `refind_x64.efi`. Disabling Secure Boot cleared custom NVRAM entries, so `refind_x64.efi` was copied over `S:\EFI\Boot\bootx64.efi` on the Windows ESP (saving `bootx64.efi.bak`) so the generic NVMe fallback boots rEFInd.

## Anaconda installer disk protection bypass

In the live desktop environment, Anaconda reported *"no disks available"*. 

This was not an Intel RST/VMD controller lock. Anaconda deliberately marks a disk read-only if it hosts the live installation source (`nvme0n1p4`).

To unlock the disk for installation:
```bash
sudo umount -l /run/initramfs/live
sudo liveinst
```
*(Alternatively, boot with `rd.live.ram` on the kernel command line to load the squashfs entirely into RAM).*

## Disk layout & dual boot

Disk size: 238.5 GB NVMe SSD.
- `p1`: 100 MB Windows ESP
- `p2`: 16 MB Microsoft Reserved
- `p3`: 100.3 GB NTFS Windows C: (BitLocker unencrypted)
- `p4`: 7 GB FAT32 `FEDORA` live installer source
- `p5`: 797 MB Windows Recovery
- Remaining ~130 GB: Unallocated space for Fedora (LUKS2 + Btrfs)

Anaconda's *"share disk with existing operating system"* mode used the unallocated space while preserving the Windows partitions and ESP.

## Post-install login & encryption model

- **Disk Encryption:** LUKS2 active on the Fedora root partition.
- **Authentication Flow:**
  1. Cold boot: Enter LUKS passphrase once to decrypt SSD.
  2. GDM auto-logs in to GNOME with a blanked keyring password (so developer tokens and browsers auto-unlock).
  3. Screen lock (<kbd>Super</kbd>+<kbd>L</kbd>) and `sudo` authenticate via the Synaptics Match-on-Chip fingerprint reader.
