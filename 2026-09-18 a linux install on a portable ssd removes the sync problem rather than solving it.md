> [!summary] eli5
> a full linux install on an external nvme ssd can be carried around and booted on whatever machine is in front of you, and this note works out what happens when you bring it home and plug it into the linux laptop.
> explored in full, nothing bought or installed: the syncing version of the idea is the hard one, the version where the laptop just boots from the ssd has no sync step at all, and there is a third route where the ssd runs as a window on the laptop instead of a reboot.
> **needs from you:** decide whether the home laptop keeps its own install or becomes a body for the ssd, recommend keeping its install as a rebuildable fallback and never trying to two-way sync the two, since two full installs kept in step by hand is the one combination that rots

> i install linux on a ssd. i take it with me, update things on it etc. then i come home, plug linux ssd into my linux laptop. and they sync. so i always have a portable desktop on ssd nvme, but can sync it with my linux laptop at any time.

**why:** [[Linux for AI and developer workflows]]

## the sync step is the expensive half of the idea and it is optional

the idea contains two separable claims, and only the first one is cheap. a linux install on an external nvme that boots on arbitrary hardware is a solved, well-trodden thing. keeping that install and a second install on the laptop in agreement with each other afterwards is the part that has defeated people for thirty years, because a running unix is not a document and does not merge.

there are three shapes this can take, and picking one up front decides everything else.

- **one install, many bodies:** the ssd is the only system you own, and the laptop, a desktop, a borrowed machine are all just a screen and a keyboard you plug it into. nothing syncs because nothing diverged. this is the strongest version and it is what the idea collapses into once you take it seriously
- **two installs, synced state:** the laptop keeps its own root, and config plus data flow between them. this only works if you accept that the package set and system state are rebuilt rather than synced, which means declaring them somewhere, and it is the shape where [[NixOS]] earns its reputation
- **ssd as a guest:** at home the ssd is not booted at all, it is passed into a [[virtual machine]] on the laptop, so the portable system appears as a window while the laptop's own session keeps running

the failure mode worth naming is the fourth shape, the one nobody chooses on purpose: two complete installs that you try to keep byte-identical with [[file sync]]. it starts working, then a package upgrade lands on one side, then a service file diverges, then you are hand-merging `/etc` at eleven at night.

## one install booting on unfamiliar hardware is four settings, not a rewrite

linux is unusually good at this compared to windows, because the kernel loads drivers at boot rather than baking them into the install. the defaults still fight you in specific, fixable ways.

- **the bootloader has to land on the ssd's own esp,** which is the classic way this goes wrong. anaconda and ubiquity both helpfully write the efi entry to the internal disk of the machine you install from, so the portable ssd then boots on exactly one computer. install with the host's internal drive physically disconnected, or drive the partitioner by hand and point the efi partition at the external disk
- **the initramfs must not be host-only.** fedora's dracut builds an initramfs containing only the storage and platform modules of the machine that built it, which is correct for a fixed laptop and fatal for a roaming disk. drop `hostonly=no` into `/etc/dracut.conf.d/` and regenerate, or on debian and ubuntu set `MODULES=most` in `initramfs.conf`
- **install the full firmware package** rather than the trimmed one, so the wifi and bluetooth chips of a host you have never seen come up without a download over the network you cannot reach yet
- **stay on a distro with a signed shim,** fedora, ubuntu or debian, so secure boot does not have to be turned off in the firmware of every machine you sit down at. asking a borrowed laptop's owner to change bios settings is where the whole plan stops being portable

filesystem mounts are already keyed by uuid on every mainstream installer, so those follow the disk without any work. the one thing that genuinely does not roam is a proprietary nvidia driver, which assumes the gpu it was built against and will drop you at a black screen on an intel or amd host, so a roaming install wants the in-tree drivers even at a performance cost. the same lesson turns up from the other direction in [[2026-08-29 installing Fedora on the Yoga without working USB ports]], where every problem was the firmware and the boot path rather than linux itself.

## encryption has to roam, which is exactly what tpm unlock cannot do

a disk that lives in a bag gets lost, so full-disk [[encryption]] is not optional here in the way it arguably is for a desktop. that rules out the comfortable modern answer, because tpm-bound unlock binds the key to one machine's chip and a roaming disk has no fixed chip.

the two options that do travel are a passphrase typed at every boot, and a fido2 token enrolled with `systemd-cryptenroll --fido2-device=auto`, which moves the secret onto something already on your keyring. the token route is the better fit, because it unlocks on any host: the hardware it depends on is in your pocket rather than in the laptop.

## the enclosure decides whether it feels like a desktop or a usb stick

this is where the idea is won or lost in daily use, and the spec sheet headline number matters less than two unglamorous properties.

- **uasp support** changes how the machine feels more than raw bandwidth does, because without it the enclosure falls back to bulk-only transport and random io collapses, which is most of what an operating system actually does
- **usb 3.2 gen 2 at 10 gbps** is the compatibility sweet spot, around 1000 mb/s and bootable from any [[USB]] c or a port. usb4 and thunderbolt enclosures are faster and will not boot on a host without those ports, which defeats the purpose
- **a metal shell,** because a bare nvme in a plastic box throttles within minutes under a real workload and you will read that as the operating system being slow
- **a drive with dram and tlc rather than a dram-less qlc one,** since this is a root filesystem taking constant small writes, not a backup target

the remaining risk is physical: an unplug while mounted is a power cut to your root disk. ext4 or btrfs journaling survives it, but it is the argument for the ssd never being the only copy of anything.

## if you keep two installs, only two of the four categories actually sync

sorting the state by how well it merges makes the boundary obvious, and the answer is that half of it should be declared rather than copied.

- **dotfiles and config** sync cleanly as a git repo with chezmoi or stow on top, because they are text and conflicts are visible
- **documents, projects and vaults** sync cleanly with [[Syncthing]] or git, which is the case that whole category of tool was built for
- **the installed package set** does not sync, it gets declared: a list in the same git repo, applied on either side. this is the seam nix removes by making the declaration the install
- **the long tail** never syncs at all. browser profiles, ssh known hosts, systemd unit state, keyrings, secrets. accept that these diverge and stop fighting it

one non-obvious perk of the single-install route is that networkmanager profiles travel with you, so every wifi network you have ever joined is already there on a machine you have never used.

## the vm route means plugging it in is not a reboot

booting the physical ssd inside qemu with the raw block device passed through, under ovmf firmware so the efi path still resolves, turns "come home and plug it in" into the portable system opening as a window next to everything already running on the laptop. nothing syncs, nothing reboots, and the two systems share a clipboard instead of a filesystem.

the constraint is that the disk can only be attached to one running kernel at a time, so the laptop must not have it mounted elsewhere, and the guest sees virtualised hardware rather than the laptop's gpu unless you go as far as passthrough. for editing files and running long jobs on the portable system while the laptop stays yours, that is a fair trade.

## what this plan does not cover

- **apple silicon hosts cannot boot it,** so a mac in the mix is a host for the vm route or for ssh, never a body for the ssd. an intel mac can be made to boot it but fights you on firmware
- **locked-down machines,** corporate laptops with secure boot enforced and usb boot disabled behind a firmware password, are out of scope, which matters because they are a large share of the machines you might want to borrow
- **the single point of failure is singular in a new way,** since one lost enclosure is your whole environment rather than one machine. that is a [[backup]] problem, not a sync problem, and the two get confused constantly
- **per-host display scaling** is the daily annoyance rather than the catastrophe, and the usual fix is a small script keyed on `/sys/class/dmi/id/product_name` that applies a per-machine profile at login

worth weighing against the whole idea: [[Tailscale + Home Assistant]] already has the ingredients for the option where you carry nothing at all and ssh home to the laptop, which has zero sync and zero hardware risk, at the cost of needing a network and the laptop staying awake. the ssd wins specifically when you want to work offline and want the machine in front of you doing the compute, which is the same pull behind [[2025-10-21 write more on location]].
