---
name: private-to-public-note-promotion
description: Standard operating procedure and safety rules for sanitizing and promoting private PKM notes into the public repository.
aliases:
  - private to public note promotion
  - sanitizing notes for public release
  - public note sanitization
created: 2026-08-27
tags:
  - technical
  - pkm
  - skill
  - workflow
  - privacy
---

# Private-to-Public Note Promotion & Sanitization

Standard operating procedure (SOP) and heuristics for taking notes, scripts, or skills from private directories and promoting them to the public vault.

---

## 🧭 Core Heuristics & Rules

### 1. 🚫 Zero Private Note Wikilinks
A public note must **never** contain a `[[wikilink]]` that points to a private note (such as notes in `work/`, private root `pkm/`, client folders, or personal daily logs).
* If a public note links to a target, that target **must exist in `public/`** or be an alias of a public note.
* Automated verification: Always run `python _scripts/check_dead_links.py <note-path>` before committing.

---

### 2. 🌲 Asymmetric Link Hierarchy (Generic vs. Specific)
**Generic concept notes must NEVER link downward to private/ephemeral specific instances.**

* **The Rule:** Downstream specific notes may link upward to generic concepts, but generic concept notes must remain evergreen, decoupled, and universally valid.
* **Bad Example:** A generic note on `[[apple]]` or `[[BLE protocol]]` linking to `[[today i ate an apple]]` or `[[Living Room Custom Motorized Blind]]`.
* **Good Example:** The specific hardware note `[[Living Room Custom Motorized Blind]]` links upward to `[[public/skills/ble-device-reverse-engineering/SKILL|ble device reverse engineering]]`, but the generic skill never mentions the specific household device.

```
┌───────────────────────────────────────────────────────────┐
│  PUBLIC / GENERIC: [[BLE GATT Protocols]]                 │
│  (Evergreen, zero private references, universal)          │
└─────────────────────────────▲─────────────────────────────┘
                              │  (Upward link is allowed)
┌─────────────────────────────┴─────────────────────────────┐
│  PRIVATE / SPECIFIC: [[Living Room Smart Blind]]          │
│  (Contains private MAC, room dimensions, household state) │
└───────────────────────────────────────────────────────────┘
```

---

### 3. 🛡️ The Context-Preservation Rule: Generalize or Flag (Don't Blindly Truncate)
When sanitizing a note, **never silently delete text if doing so destroys vital context, technical reasoning, or nuance**.

Follow this decision tree:

```
[ Private Reference Encountered ]
               │
               ▼
Can the insight be safely generalized?
       ├──▶ YES ──▶ Extract/rewrite as a generic public concept or parameter.
       │            (e.g. Replace specific MAC address with `--mac <DEVICE_MAC>` argument).
       │
       └──▶ NO  ──▶ Retain note in private OR flag for human review:
                    <!-- TODO(public-review): Redacted private reference to [[Internal Project]]. Requires abstraction or human decision. -->
```

* **Abstraction Example:** If a note references a private bug in a commercial codebase, rewrite the paragraph to explain the underlying class of bug (e.g. *race condition in SQLite WAL under multi-threaded keepalives*) rather than deleting the lesson.
* **Flagging Example:** If abstracting the reference would distort the factual claim, leave a visible HTML review comment and keep the note in private staging until approved.

---

### 4. 🧹 Absolute Paths & Personal Identity Scrubbing
Ensure zero leakage of workstation environments or identities:
* **Scrub User Paths:** Replace `C:\Users\<username>\...` or `/home/<username>/...` with generic relative paths (`./scripts/`) or standard environment placeholders (`$HOME`, `%USERPROFILE%`).
* **Scrub Usernames & Names:** Ensure personal names (family, partner, friends, client names, employer names) are never published.
* **Scrub Git Author Identities:** Verify local repo author configs before pushing (`git config user.name`).

---

### 5. 🔑 Credentials, Secrets & Telemetry Scrubbing
* **Zero API Keys & Tokens:** Ensure no `ghp_`, `gsk_`, `sk-`, or bearer tokens exist in markdown notes or script defaults.
* **Zero Physical Telemetry:** Scrub hardware MAC addresses, private Wi-Fi SSIDs, internal LAN IP addresses (`192.168.x.x`, `10.x.x.x`), and household location/sensor telemetry.
* **Parameterize Scripts:** Convert hardcoded private values into CLI flags (e.g. `--mac`, `--token`, `--vault`).

---

### 6. 🔍 The "Diff-First Approval Loop" (Review Before Writing)
* **Never silently rewrite or assume:** When sanitizing personal, medical, financial, or employer-specific references in a note, always present a clear before-and-after diff of the proposed generalizations to the human for explicit review before modifying or moving the file.

---

### 7. ⚠️ Obsidian In-Memory Tab Management
* **The Root Recreation Trap:** If a file is moved on disk (from root `pkm/` to `public/`) while it is actively open in an Obsidian tab, Obsidian retains the in-memory tab buffer pointing to the old root path. When Obsidian autosaves, it may re-create the deleted file in root.
* **The Protocol:** Whenever moving an open note to `public/`:
  1. Move and commit the file to `public/` and remove from root.
  2. Close the open tab in Obsidian (`Ctrl + W`).
  3. Reopen the note via Quick Switcher (`Ctrl + O`) from its new `public/` path to bind the editor to the new location.

---

## 📋 The Pre-Publishing Verification Checklist

Before running `git add public/...`:

1. [ ] **Scan for Private Strings:** Run regex audit for username, private repository names, and secret token patterns.
2. [ ] **Draft Proposed Generalizations:** Present a before-and-after diff of sensitive lines for human review and approval.
3. [ ] **Verify Wikilinks:** Run `python _scripts/check_dead_links.py <note-path>` and confirm `[PASS]` (ignoring backticked code examples).
4. [ ] **Check Link Directionality:** Confirm generic concept notes do not link downward to ephemeral or private notes.
5. [ ] **Context Check:** Confirm that no vital technical nuances were lost during redacting/generalizing.
6. [ ] **Obsidian Buffer Refresh:** Close any open Obsidian tabs for the file before or immediately after the move.
7. [ ] **Daily Note Indexing:** Add the new public note link to today's daily note under the appropriate section.
8. [ ] **Dual Commit:** Commit inside `public/`, push `origin main`, then commit the submodule pointer in root `pkm/` and push `origin main`.

---

## 🔗 Related Notes & Skills
- [[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]
- [[public/skills/ble-device-reverse-engineering/SKILL|ble device reverse engineering]]
- [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]]
- [[public/Obsidian Git - device author identity|Obsidian Git - device author identity]]
