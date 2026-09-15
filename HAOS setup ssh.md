---
aliases:
- HAOS ssh
- ssh to home assistant
tags:
- technical
---

ssh into a [[HAOS]] box, and the thing worth knowing first is that **there are three different shells** behind the word "ssh" here and they are not interchangeable. picking the wrong one is the usual reason a working key still cannot see the file you want.

| shell | port | reaches |
| --- | --- | --- |
| **Terminal & SSH** add-on (`core_ssh`) | 22 | the add-on's own container and the `ha` cli, [not the host filesystem](https://www.home-assistant.io/common-tasks/os/) |
| **Advanced SSH & Web Terminal** (`a0d7b954_ssh`) | 22 | same, plus the host's docker and `login` when protection mode is off |
| **host debug shell** | 22222 | the real HAOS host as root |

## terminal & ssh, the official add-on

install **Terminal & SSH** from the add-on store, open its configuration tab, put a public key in `authorized_keys`, save and start. that is the whole path for most uses, and it is the one to reach for unless you specifically need the host.

it gives the `ha` cli (`ha core restart`, `ha host reboot`, `ha supervisor reload`) and the usual editors, and it deliberately does not mount the host filesystem.

## advanced ssh & web terminal, the community add-on

the [community add-on](https://github.com/hassio-addons/addon-ssh) is the one to install when you need the host's docker or the `login` command. its options, [documented in full here](https://github.com/hassio-addons/addon-ssh/blob/main/ssh/DOCS.md):

```yaml
ssh:
  username: homeassistant
  password: ""
  authorized_keys:
    - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... you@yourmachine
  sftp: false
  compatibility_mode: false
```

`username` is lowercased and `root` is possible but discouraged, except that **sftp only works as `root`**. an empty `password` disables password auth, which is what you want once a key works. `packages` and `init_commands` survive restarts, which is how you keep a tool installed.

**protection mode has to be off** for this add-on to reach the host's docker or the `ha` cli, and that is a real privilege grant rather than a formality — the toggle is on the add-on's info page.

## authorized_keys is an option, not a file

the single most wasted hour here: the add-on **rewrites `~/.ssh/authorized_keys` from its options on every start**, so a key appended to the file by hand works until the next restart and then silently vanishes. always put the key in the add-on's configuration.

if you are setting that option through the supervisor api rather than the ui, note that an options post **replaces the whole options object** rather than merging into it. sending only `authorized_keys` fails validation with `Missing option 'apks' in root`. read the current options from `/addons/<slug>/info`, change the one key, send the whole dictionary back.

## the client side

follow [[generate SSH key]], but make a dedicated key rather than reusing the github one, so revoking the box does not touch anything else:

```sh
ssh-keygen -t ed25519 -f ~/.ssh/ha_ed25519 -C "laptop->haos" -N ""
```

then `~/.ssh/config` carries the rest, so the connection is just `ssh haos`:

```
Host haos
  HostName 192.168.1.10
  User root
  Port 22
  IdentityFile ~/.ssh/ha_ed25519
  IdentitiesOnly yes
```

**`IdentitiesOnly yes` matters** once there is more than one key in the agent. without it ssh offers each key in turn, the add-on hits `MaxAuthTries`, and the connection is refused before the correct key is ever tried — which reads exactly like a bad key.

**`User root` is correct here** and is not the host's root, it is the add-on container's own user.

## the host shell on port 22222

the [host debug shell](https://developers.home-assistant.io/docs/operating-system/debugging/) is a separate thing with a deliberately awkward setup, because it is full root on the OS. it cannot be enabled from the ui at all — the key has to arrive on a usb drive:

- the partition must be **labelled `CONFIG`**, case sensitive, formatted FAT, ext4 or NTFS
- the file at its root must be named **`authorized_keys`**, no extension, not `.pub`
- it must use **LF line endings, not CRLF**, and be plain ASCII, so a comment with a non-ascii character in it breaks the whole file
- insert the drive and run `ha os import`, or reboot with it attached

then `ssh root@homeassistant.local -p 22222`, landing in `/root`. removing the file from the drive and rebooting disables port 22222 again.

## two things that look like broken keys and are not

**the box answers ssh only while the add-on is running.** port 22 belongs to the add-on, not to HAOS, so a stopped or crashed add-on gives connection refused on an otherwise perfect setup.

**`homeassistant.local` can resolve to ipv6 first.** mdns advertises a link-local `fe80::` address, and a docker-published port usually listens on ipv4 only, so the connection is accepted and then immediately reset — `Recv failure: Connection reset by peer`, while `nc` to the ipv4 address on the same port succeeds. use the ipv4 literal, or test with `curl -4`.

[[check ssh github connection]] is the same `-T` verification idea if a key stops working later. for file access rather than a shell, [[HAOS setup samba]] is usually the easier answer, and [[HAOS setup mcp|mcp]] is the one to use for letting an agent control the house rather than administer the box.
