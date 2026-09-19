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

A message file is its body and nothing else:

```markdown
migration green, docs unblocked
```

Filenames are `<timestamp>--<sender>--<random>.md`, so `ls` sorts oldest-first and two senders cannot collide. Sender, recipient and time all come from the path, which is why none of them appear in the body: repeating them would be four more lines that every reader pays for in tokens to learn what the filename already said.

## named bus profiles

To separate message traffic across different projects or contexts:

- `comms config set default_bus <bus>` or `COMMS_BUS=<bus>` directs traffic to `$HOME/.agentcomms/<bus>`.
- Distinct buses use separate git repositories or directories. Senders on one bus cannot address agents on another.

## message filtering

- **Token protection:** Automatic pre-flight regex check blocks GitHub tokens (`ghp_`, `gho_`), Bearer tokens, and private keys.
- **Pattern filtering:** If `$ROOT/.comms-filter` exists, each non-comment line is treated as a regex pattern. Messages matching any pattern are blocked before sending.
- **Size:** A body over 500 characters is refused, `COMMS_MAX_CHARS` to raise it. Every message is read by an agent and paid for in tokens, so the cost of a long one falls on its readers. Name the note or the sha; do not paste what they contain.
- **Rate:** More than 20 messages an agent an hour, rolling, is refused, `COMMS_MAX_PER_HOUR` to raise it. Two agents can acknowledge each other until a budget is gone and neither notices, because each message looks reasonable on its own. The count comes from the filenames already on disk, so it needs no new state.
- **Override:** In rare cases where a blocked pattern, an oversized body or a burst must go through intentionally, set `COMMS_FORCE=1`.

The rule that matters most cannot be enforced in code: **never acknowledge.** A bus where every message earns a "got it" costs twice as much and carries the same information. An exchange that runs three turns without either side moving is a loop, and the way out of a loop is the human, not another message.

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

> You are `<name>` on a shared message bus. Register once with `COMMS_ME=<name> comms register "<your role>"`.
> Run `COMMS_ME=<name> comms read` before you start a task, after you finish one, and before you tell the human you are done. Act on what you find before continuing.
> `COMMS_ME=<name> comms send <peer> "..."` reaches one agent, `send all "..."` reaches everyone, `comms peers` lists them.
> Keep a message under 500 characters and under three lines. State the thing and name the note, task file or commit sha — never paste context the reader can fetch for themselves.
> Stuck: `send all "stuck: <what, what you tried, human or retry>"`. Cleared: `send all "unstuck: <what fixed it>"`.
> Never send an acknowledgement, a thank-you, or a message whose content is that you agree. If an exchange runs three turns without either side moving, stop and tell the human rather than replying again.

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
