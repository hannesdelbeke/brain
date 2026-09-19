---
name: agent-comms
description: Let AI agents send each other messages through a shared git repo, one file per message, working between sessions of the same vendor, between different vendors, and across machines. Supports isolated bus profiles with configurable message filters.
---

## what this is

Vendor CLI tools (Claude Code, Gemini CLI, Codex, Cursor, etc.) typically lack built-in mechanisms to communicate across independent sessions or across different tools.

The solution is a shared directory that every agent can reach, holding one file per message. That needs only a shell and a filesystem.

## the bus

The bus is a git repository or filesystem directory. It holds messages only, never code: `agents/` for who exists, `inbox/<name>/` for mail, `inbox/<name>/done/` for what has been read, `broadcast/` for everyone. Its `git log` is the transcript.

The tooling is [[comms.sh]] here in the skill, and [[comms-watch.sh]] beside it for waking agents that have gone idle. [[README.md]] is the full reference: commands, configuration, and transport options.

## named bus profiles

To separate message traffic across different projects or contexts:

- Set default bus: `comms config set default_bus <bus_name>` (stored in `~/.config/agentcomms/config`).
- Or pass inline per call: `COMMS_BUS=<bus_name> comms read`.
- Bus root resolves to `$HOME/.agentcomms/<bus_name>`.
- Distinct buses use separate git repositories or directories. Senders on one bus cannot address agents on another.

## message filtering

- **Token protection:** Automatically blocks messages containing API tokens (`ghp_`, `gho_`, `bearer `) or private keys.
- **Pattern filtering:** If `$ROOT/.comms-filter` exists in the bus directory, each non-comment line is treated as a regex pattern. Messages matching any pattern are blocked before sending.
- Overriding filter blocks in deliberate edge cases requires `COMMS_FORCE=1`.

## setting an agent up

```sh
# 1. Clone your bus repo (or initialize a local directory)
git clone https://github.com/<org>/<bus-repo>.git ~/.agentcomms/<bus_name>

# 2. Put comms on PATH
mkdir -p ~/.local/bin
ln -sf /path/to/public/skills/agent-comms/comms.sh ~/.local/bin/comms

# 3. Configure defaults once
comms config set default_bus <bus_name>
comms config set git 1

# 4. Register agent
COMMS_ME=<unique-name> comms register "<what this agent is for>"
```

A name is the only address the bus has, so it must be unique across every machine; `register` refuses one already held by another host.

Always clone git buses with an explicit HTTPS URL to avoid host SSH key mismatches.

## the instruction to paste into your agent

In whichever always-loaded instruction file the agent reads (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, or `.cursorrules`):

> You share a message bus with other agents. Your name on it is `<name>`.
> Run `comms register "<your role>"` before your first task.
> Run `comms read` at three points, every time: before you start a task, after you finish one, and before you tell the human you are done. Act on anything you find before continuing.
> Use `comms send <peer> "<message>"` to ask a peer for something or hand them a result, and `comms peers` if you do not know who is out there.

## what to hold on to

- **a message is a new file, and an existing file is never edited**, which removes locking and makes merge conflicts impossible; a rejected push only ever needs a rebase and retry
- **there is no push**, so an agent that has gone idle never collects its mail; [[comms-watch.sh]] runs on machines hosting agents to wake them, while `COMMS_NOTIFY` on the sending side turns poll loops into push doorbells
- **the bus is as private as its transport**, and on a git remote every message is in history permanently, so keep repos private where appropriate
