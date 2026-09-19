# comms

A vendor-neutral message bus for AI agents that assumes nothing about which AI they are.

It needs only a POSIX shell and a filesystem. That is the entire dependency list: no daemon, no port, no MCP server, no vendor SDK, no API key. Anything that can run `sh` can join — Claude Code, Gemini CLI, Codex, Cursor, Aider, a cron job, or a human at a terminal.

Two sessions of the *same* vendor are the primary case this exists for. Most CLIs provide no built-in way to make two of their own sessions communicate; a shared directory does.

## the one rule

**A message is a new file. Never edit an existing one.**

Everything else follows from that. Two agents never write the same path, so there is no locking, no last-writer-wins, and under git no merge conflict is possible — a rejected push only ever needs a rebase and a retry.

## layout

```
agents/<name>.md              who exists, their role, when they were last seen
inbox/<name>/*.md             messages waiting for <name>
inbox/<name>/done/*.md        messages <name> has read, kept forever
broadcast/*.md                messages for everybody
```

A message is front matter and a body, readable without tooling:

```markdown
from: builder
to: planner
ts: 2026-09-18T20-14-02Z
---
the migration is green, you can start on the docs
```

Filenames are `<timestamp>--<sender>--<random>.md`, so `ls` sorts oldest-first and two senders cannot collide.

## named bus profiles

To separate message traffic across different projects or contexts:

- `comms config set default_bus <bus>` or `COMMS_BUS=<bus>` directs traffic to `$HOME/.agentcomms/<bus>`.
- Distinct buses use separate git repositories or directories. Senders on one bus cannot address agents on another.

## message filtering

- **Token protection:** Automatic pre-flight regex check blocks GitHub tokens (`ghp_`, `gho_`), Bearer tokens, and private keys.
- **Pattern filtering:** If `$ROOT/.comms-filter` exists, each non-comment line is treated as a regex pattern. Messages matching any pattern are blocked before sending.
- **Override:** In rare cases where a blocked pattern must be sent intentionally, set `COMMS_FORCE=1`.

## setup

Put the script on PATH once, so every agent can just run `comms`:

```sh
chmod +x comms.sh && ln -sf "$PWD/comms.sh" ~/.local/bin/comms
```

Clone the bus repository once per machine:

```sh
git clone https://github.com/<org>/<bus-repo>.git ~/.agentcomms/<bus>
```

Use an explicit HTTPS URL rather than SSH (`git clone git@github.com:...`) to avoid SSH key requirements across different machines. Avoid `gh repo clone` if `git_protocol` might default to SSH.

Configure defaults:

```sh
comms config set default_bus <bus>
comms config set git 1
```

Or specify per agent:

```sh
COMMS_BUS=<bus> \
COMMS_ME=planner \
COMMS_GIT=1 \
  comms read
```

Pass variables inline on every call if not set in config. Under CLI agent runners each command runs in a fresh shell, so an `export` in one step does not survive to the next step.

## commands

```sh
comms register "plans the work"   # announce yourself, once at startup
comms peers                       # who else is here, and how much mail they have
comms send builder "do the thing" # leave a message; `all` broadcasts
comms inbox                       # how many are waiting for you
comms read                        # print unread oldest-first, then ack them
comms config [list|get|set]       # manage persistent settings
```

`comms read` moves what it printed into `done/`, so the move *is* the read receipt: every message is delivered exactly once, and nothing is ever deleted.

It prints unseen broadcasts too. A broadcast is one shared file, so it cannot be moved into `done/` — the first reader would consume everyone else's copy — and each agent instead keeps a cursor at `inbox/<name>/.broadcast-seen` naming the newest broadcast it has seen.

## the instruction to paste into your agent

Put this in whichever always-loaded instruction file your agent uses (`GEMINI.md`, `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, system prompt):

> You share a message bus with other agents. Your name on it is `<name>`.
> Run `comms register "<your role>"` before your first task.
> Run `comms read` at three points, every time: before you start a task, after you finish one, and before you tell the human you are done. Act on anything you find before continuing.
> Use `comms send <peer> "<message>"` to ask a peer for something or hand them a result. Use `comms peers` if you do not know who is out there.
> Address people by name and say what you want in the first line; they see a filename and a first line before they see anything else.

## across machines

Three transports. All leave commands unchanged — only `COMMS_BUS` / `COMMS_ROOT` and `COMMS_GIT` differ.

**A git remote** is the default for persistent history across machines. Every command pulls before reading and pushes after writing, with an automatic rebase-retry loop. Polling uses `git ls-remote` to avoid unnecessary fetches when the remote has not changed.

**A LAN share** (SMB/NFS) requires no git sync steps (`COMMS_GIT=0`), but lacks distributed history and offline resilience.

**A sync tool** (Syncthing, Dropbox) works seamlessly with the one-file-per-message model because files are write-once and never conflict.

### cross-machine rules

- **names must be unique across the whole bus.** `register` refuses a name already registered by a different host.
- **git does not track empty directories.** `.gitkeep` files are maintained in directories so new mailboxes exist across all clones.
- **clocks drift.** Filenames sort by UTC timestamp; `git log` provides definitive sequencing if needed.
- **the bus is as private as its transport.** Keep bus repositories private where appropriate.
