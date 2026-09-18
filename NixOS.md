---
aliases:
- nix
- nix-os
- home-manager
tags:
- technical
- linux
- os
---

a linux distribution where the whole machine is described in one declarative config file rather than assembled by running install commands over time.

`configuration.nix` lists the packages, services and settings, and `nixos-rebuild` makes the machine match it. every build is a new generation you can roll back to at boot, so an upgrade that breaks something is undone rather than repaired.

what it buys over an ordinary distro:
- **rebuilding a machine from scratch** is applying the config, not remembering what you installed, which is the seam that makes a second machine cheap to keep in step
- **home-manager** does the same for the user's dotfiles and per-user packages, so the config covers the desktop as well as the system
- **the cost** is that packaging anything unusual means learning the nix language, and binaries that expect a normal filesystem layout need patching

relevant to [[2026-09-18 a linux install on a portable ssd removes the sync problem rather than solving it]], where declaring the package set is the only part of two-machine state that does not sync on its own.
