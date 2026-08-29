---
aliases:
- terminal multiplexing
- tmux
- zellij
created: 2026-08-29
tags:
- technical
- tools
- cli
---

A tool that runs multiple terminal sessions inside a single window and keeps processes alive in the background when you disconnect.

## Why use one

Standard SSH connections kill running processes when the network drops or you close your laptop. A multiplexer runs the shell in a background daemon:
- **Session persistence**: disconnect anytime, processes keep running. Reattach later from any machine.
- **Split panes**: tile multiple terminal views side by side.
- **Shared sessions**: attach multiple clients to the same shell for remote pair programming or monitoring.

## Common tools

- **tmux** — standard on Linux, macOS, and WSL. Scriptable with extensive keybinding ecosystems.
- **zellij** — modern Rust alternative with native Windows support, built-in layout management, and discoverable UI tips.
- **screen** — legacy Unix multiplexer, ubiquitous on older servers.

## Agent workflow

For long-running AI coding tools like Claude Code:
1. Start the agent in a named session on the host: `zellij --session ai` or `tmux new -s ai`.
2. Detach or close connection (`Ctrl+q` / `Ctrl+b d`).
3. Reattach over SSH from phone, laptop, or web: `zellij attach ai` or `tmux attach -t ai`.
