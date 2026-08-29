---
aliases:
- Linux developer workflow
- Linux for AI development
created: 2026-08-29
tags:
- technical
- linux
- os
- dev-environment
---

Why moving to Linux solves common developer and agentic coding bottlenecks, and practical transition paths.

## Why Linux fits AI agent development

- **Native POSIX tooling** — AI agents (Claude Code, Codex, Antigravity) generate standard bash, `grep`, `sed`, `git`, and python commands. Linux avoids Windows PowerShell quote escaping, path slash issues, and CRLF line-ending corruption.
- **First-class [[terminal multiplexer]] support** — Native `tmux` runs out of the box with zero setup. Scriptable session control (`tmux send-keys`) enables headless automation and phone/remote control.
- **Fast filesystem I/O** — ext4/btrfs handles thousands of small files (`node_modules`, `.git`, Python venvs, SQLite indexes) significantly faster than Windows NTFS.
- **ThinkPad compatibility** — Lenovo ThinkPads have near-flawless Linux kernel and driver support (suspend, battery management, trackpoint).
- **Native containerization** — Docker runs directly on the Linux kernel without the Hyper-V / WSL2 memory virtualization layer.

## Trade-offs to consider

- **DCC & proprietary creative software** — Blender and Houdini run natively on Linux. Maya has official Linux builds (RPM). Adobe tools (Photoshop) require Windows/VMs.
- **Gaming & anti-cheat** — Steam Proton runs most games natively, but titles with kernel-level Windows anti-cheat don't work.

## Practical transition path

1. **Step 1 (Zero-risk)**: Use WSL2 + `tmux` on Windows for all coding and CLI agents.
2. **Step 2 (ThinkPad migration)**: Install Fedora Workstation or Ubuntu LTS on the personal ThinkPad. Use it as the daily portable driver.
3. **Step 3 (Hybrid setup)**: Keep the work desktop (Dell) on Windows for proprietary tools, accessed remotely over SSH or Tailscale from the Linux ThinkPad.

## Related notes
- [[terminal multiplexer]] — background daemon session management
- [[command line interface]] — text-based terminal concepts
- [[AI session]] — interactive agent session structures
