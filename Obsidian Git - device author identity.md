---
tags:
- technical
- git
- obsidian
---

When syncing an [[Obsidian]] vault across multiple laptops and desktops with the `obsidian-git` plugin, it is useful to know which physical machine authored an automated backup commit (e.g. `Obsidian Blade` vs `Obsidian ThinkPad`).

Because `.obsidian/plugins/obsidian-git/data.json` is shared and committed to the repository, setting custom commit message templates in Obsidian settings will overwrite other devices.

Instead, configure the author name at the local [[Git]] repository level (`.git/config`).

## How it Works
On desktop operating systems, `obsidian-git` executes standard CLI `git commit`. Git resolves the author name in the following priority order:
1. **Local repository config** (`<repo>/.git/config`) — *Overrides everything for this repo only.*
2. **Global user config** (`~/.gitconfig`) — *Machine-wide fallback.*

Setting `user.name` locally inside the vault ensures:
- Obsidian auto-backup commits are tagged with the specific device name.
- Global developer configuration (`user.name = "Hannes Delbeke"`) remains untouched for all other programming repositories.
- Local repository configs are never committed or pushed to remote repositories.

## Configuration Commands

Set the author name locally on the root vault:
```bash
git config --local user.name "Obsidian ThinkPad"
```

Apply across all submodules:
```bash
git submodule foreach --recursive 'git config --local user.name "Obsidian ThinkPad"'
```

Verify settings:
```bash
git config --local --get user.name
```

ensure this doesn't clash with ai agent authorship [[github co-authors for AI]]

[[provenance]]
[[git author]]