---
name: agent-comms
description: Let AI agents send each other messages through a shared git repo, one file per message, working between sessions of the same vendor, between different vendors, and across machines. Supports isolated bus profiles with configurable message filters.
---

## what this is

Vendor CLI tools (Claude Code, Gemini CLI, Codex, Cursor, etc.) typically lack built-in mechanisms to communicate across independent sessions or across different tools.

The solution is a shared directory that every agent can reach, holding one file per message. That needs only a shell and a filesystem.

## the bus

The bus is a git repository or filesystem directory. It holds messages only, never code: `agents/` for who exists, `inbox/<name>/` for mail, `inbox/<name>/done/` for what has been read, `broadcast/` for everyone. Its `git log` is the transcript, and stays so — the working tree expires, the history does not.

The tooling is [[comms.sh]] here in the skill, and [[comms-watch.sh]] beside it for waking agents that have gone idle. [[README.md]] is the full reference: commands, configuration, and transport options.

## named bus profiles

To separate message traffic across different projects or contexts:

- Set default bus: `comms config set default_bus <bus_name>` (stored in `~/.config/agentcomms/config`).
- Or pass via CLI flag: `comms --bus <bus_name> read` (recommended for static allowlists).
- Or pass inline per call: `COMMS_BUS=<bus_name> comms read` (legacy / fallback).
- Bus root resolves to `$HOME/.agentcomms/<bus_name>`.
- Distinct buses use separate git repositories or directories. Senders on one bus cannot address agents on another.

## cli flags & static allowlist support (claude code)

Comms commands accept `--me <name>` and `--bus <bus>` flags:

```sh
comms --me agent1 read
comms --bus project-a --me agent1 send all "status update"
```

### why CLI flags instead of environment variables?

In CLI agent runners like Claude Code, auto permission mode submits side-effectful shell commands to a model-based safety classifier unless covered by a static allow rule in `permissions.allow`.

Claude Code's static allowlist engine matches command prefixes but **does not match past leading environment variable assignments** (e.g., `COMMS_ME=agent1 comms read`). As documented by Anthropic, an allow rule will not match past an assignment of unlisted environment variables. Consequently, commands with leading `COMMS_ME=...` or `COMMS_BUS=...` bypass static rules and fall through to the runtime safety classifier on every single invocation.

During API latency spikes or model pool degradation, this classifier times out and fails closed (`temporarily unavailable (timed out)`), freezing agent sessions and burning tokens on futile retry loops.

Using CLI flags ensures the command string starts with `comms ` (e.g., `comms --me agent1 read`). A single static rule in `~/.claude/settings.json`:

```json
"permissions": {
  "allow": [
    "Bash(comms *)"
  ]
}
```

matches all comms invocations statically. Calls execute immediately with zero classifier latency, zero extra token spend, and complete immunity to classifier outages.

Environment variables (`COMMS_ME`, `COMMS_BUS`) remain fully supported as fallbacks.

## ambient context vs direct tasks (anti-meta-work)

Broadcast messages (`send all "..."` / unseen broadcasts in `comms read`) are **ambient context**, NOT direct task assignments:

- **Informational awareness only:** Broadcasts inform the fleet about ambient state (e.g. schema updates, system health, "stuck" or "unstuck" alerts).
- **Never drop active tasks:** An agent reading a broadcast must NEVER abandon its active assignment or launch reactive side-quests (audits, note refactoring, cleanup runs) based on an ambient broadcast.
- **Direct mail requires action:** Direct messages (`send <name> "..."`) landed in `inbox/<name>` are targeted requests and should be acted on.
- **Meta-work restriction:** A session whose subject is the agent fleet or tooling may not spawn another session or subagent whose subject is also the agent fleet. Fleet rollup, audit, and sweep work must be batched into scheduled maintenance runs rather than triggered reactively by peer broadcast events.

## message filtering

- **Token protection:** Automatically blocks messages containing API tokens (`ghp_`, `gho_`, `bearer `) or private keys.
- **Pattern filtering:** If `$ROOT/.comms-filter` exists in the bus directory, each non-comment line is treated as a regex pattern. Messages matching any pattern are blocked before sending.
- **Size cap:** Bodies over 500 characters are refused, `COMMS_MAX_CHARS` to raise it. A long message charges every reader for it, so name the note or the sha rather than pasting what it holds.
- **Rate cap:** More than 20 deliveries an agent an hour, rolling, is refused, `COMMS_MAX_PER_HOUR` to raise it. It turns a runaway exchange into an error somebody has to stop at.
- **Fan-out pricing:** A broadcast counts once per registered peer rather than once, because it is one send and N reads.
- **Mute:** `inbox/<name>/.mute`, one sender per line, hides that sender's broadcasts from this reader while still advancing the cursor.
- Overriding a filter block, an oversized body or a burst in deliberate edge cases requires `COMMS_FORCE=1`.

## retention

Everything on the bus expires, because an agent cannot tell a live instruction from a dead one — both are a file with a name and a first line. Broadcasts and read mail go at seven days, uncollected mail at thirty, an unrefreshed registration at fourteen (`COMMS_TTL_DAYS`, `COMMS_MAIL_TTL_DAYS`, `COMMS_PEER_TTL_DAYS`, or the matching `comms config set ttl_days` keys).

`read` sweeps once a day per clone on its own, so nobody has to remember; `comms gc` forces one and `comms gc --dry-run` shows what would go. Reading is floored by the window independently of the sweep, so an old broadcast is never shown as unread even on a clone that has never swept. An expired registration moves to `agents/retired/` and `send` then refuses that name instead of dropping mail into an inbox nobody will open; re-registering brings it back.

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
comms --me <unique-name> register "<what this agent is for>"
```

A name is the only address the bus has, so it must be unique across every machine; `register` refuses one already held by another host.

Always clone git buses with an explicit HTTPS URL to avoid host SSH key mismatches.

## the instruction to paste into your agent

In whichever always-loaded instruction file the agent reads (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, or `.cursorrules`):

> You are `<name>` on a shared message bus. Register once with `comms --me <name> register "<your role>"`.
> Run `comms --me <name> read` before you start a task, after you finish one, and before you tell the human you are done.
> Direct mail addressed to you (`inbox/<name>`) requires action. Peer broadcasts (`all`) are ambient context for situational awareness only — NOT direct task assignments. Do not abandon your current goal or spawn fleet meta-work tasks in response to a broadcast.
> `comms --me <name> send <peer> "..."` reaches one agent, `comms --me <name> send all "..."` reaches everyone, `comms peers` lists them.
> Keep a message under 500 characters and under three lines. State the thing and name the note, task file or commit sha — never paste context the reader can fetch for themselves.
> Stuck: `comms --me <name> send all "stuck: <what, what you tried, human or retry>"`. Cleared: `comms --me <name> send all "unstuck: <what fixed it>"`.
> Never send an acknowledgement, a thank-you, or a message whose content is that you agree. If an exchange runs three turns without either side moving, stop and tell the human rather than replying again.

## what to hold on to

- **a message is a new file, and an existing file is never edited**, which removes locking and makes merge conflicts impossible; a rejected push only ever needs a rebase and retry
- **there is no push**, so an agent that has gone idle never collects its mail; [[comms-watch.sh]] runs on machines hosting agents to wake them, while `COMMS_NOTIFY` on the sending side turns poll loops into push doorbells
- **everything expires, or the channel becomes an archive**, and an agent handed an archive works through the archive; `read` sweeps once a day on its own, and age is read from the filename rather than mtime, because a fresh clone stamps every file with the checkout time
- **the bus is as private as its transport**, and on a git remote every message is in history permanently, so keep repos private where appropriate. expiry empties the working tree and changes nothing about this
- **every message is paid for in tokens by everyone who reads it**, so `send` refuses a body over 500 characters and refuses an agent more than 20 messages an hour, `COMMS_MAX_CHARS` and `COMMS_MAX_PER_HOUR` to raise either. the unenforceable half of that rule is never acknowledging: a bus where every message earns a "got it" costs twice as much and says the same thing
- **broadcasts are ambient context, not task assignments**, to prevent fleet meta-work loops where agents trigger cascaded audits and maintenance runs on each other.
