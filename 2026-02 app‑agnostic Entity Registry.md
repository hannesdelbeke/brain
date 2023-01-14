
[[AI article]] created from [[Obsidian auto complete app URI]]

you’re circling around a _unified data‑layer_ that sits **outside** [[Obsidian]], outside [[Google]], outside [[Strava]], outside [[GitHub]] — and acts as a **resolver**, **index**, and **link registry** for _everything you own_.  
[[Obsidian autocomplete]] is just one _client_ of that system, not the system itself.

# 🧩 The Core Idea

A **generic, app‑agnostic “Entity Registry”** that:

- Stores _entities_ (contacts, notes, photos, posts, repos, activities…)
- Stores _URIs_ for each entity, across multiple apps
- Exposes a **local API** for autocomplete, linking, syncing
- Can be backed up, queried, and extended with plugins
- Never forces you to modify the original data sources
- Lets Obsidian (or any editor) subscribe to its suggestions

Think of it as:

> **A personal, local, open-source “link resolver + metadata index” for your entire digital life.**

This is _not_ a wrapper around Obsidian.  
Obsidian is just one consumer.

---

# 🏗️ Architecture Overview

## 1. **The Registry (Local Database)**

A small local DB (SQLite or LiteFS) with tables like:

|Table|Purpose|
|---|---|
|`entity`|Unique ID, type (`contact`, `note`, `photo`, `repo`, `activity`, …)|
|`source_uri`|URIs from external systems (Google Contacts, Strava, GitHub…)|
|`local_uri`|Local app URIs (Obsidian, local photos, local notes)|
|`metadata`|JSON blob: names, tags, timestamps, relationships|
|`backlinks`|Optional: links between entities|

This DB is the **single source of truth** for linking.

### Why SQLite?

- Portable
- Easy to back up
- Easy to sync
- Zero dependencies
- Works on all platforms
- Perfect for plugin systems

---

## 2. **Plugin System**

Each plugin is responsible for:

### **a) Importing / syncing external data**

Examples:

- Google Contacts → list of contacts
- Google Photos → list of photos
- Strava → list of activities
- GitHub → repos, issues, PRs
- Obsidian → notes, files

Each plugin maps external objects → registry entities.

### **b) Providing URIs**

Each plugin defines how to open an entity:

- Google Contacts → `https://contacts.google.com/...`
- Obsidian → `obsidian://open?vault=...&file=...`
- Instagram → `instagram://media?id=...`
- Strava → `strava://activity/12345`
- GitHub → `github://repo/...` or `https://github.com/...`

### **c) Optional: write-back**

For example:

- Sync Obsidian metadata → Google Contacts notes field
- Sync Strava activity name → Obsidian note title
- Sync GitHub repo topics → Obsidian tags

But this is optional and can be disabled.

---

## 3. **Autocomplete Provider**

Expose a simple local API:

```
GET /search?q=han
```

Returns:

```
[
  { "label": "Hannes (Google Contact)", "uri": "app://contact/123" },
  { "label": "Hannes – Personal Note", "uri": "obsidian://..." }
]
```

Obsidian plugin → calls this API → injects suggestions into the link autocomplete.

This keeps Obsidian **decoupled** from the data logic.

---

# 🔄 Sync Model

Each plugin defines:

- **pull**: import external data
- **push** (optional): write metadata back
- **resolve**: generate URIs
- **merge**: deduplicate entities across sources

Example:  
A Google Contact and an Obsidian note both represent “Alice”.

The registry merges them into one entity with multiple URIs.

---

# 🗄️ Backup Strategy

Because everything is local and open:

### **1. SQLite file backup**

Just copy the DB file.  
You can version it with Git, Syncthing, or restic.

### **2. Plugin-specific exports**

Each plugin can optionally export:

- Google Contacts → `.vcf`
- Strava → `.json`
- GitHub → `.json`
- Obsidian → already local

### **3. Full registry export**

A single `.json` or `.zip` containing:

- DB dump
- Plugin metadata
- Config

This makes the system portable and future-proof.

---

# 🧠 Does this solve your earlier problems?

## ✔️ Interwikilinks plugin

Yes — this becomes a **generalized interwiki resolver**.

## ✔️ Linking contacts to photos, memories, notes

Yes — the registry stores relationships.

## ✔️ Note linking duplicate source

Yes — because the registry merges entities across sources.

## ✔️ Backlinks everywhere

You don’t need to modify Google Photos or Contacts.  
Backlinks live in the registry, not in the source systems.

---

# 🧪 First Implementation: Google Contacts Wrapper

Start with:

- Fetch contacts via Google API
- Store them in the registry
- Generate URIs
- Expose them to Obsidian autocomplete

Then expand to:

- Google Photos
- Strava
- GitHub
- Instagram
- Local photo drive
- Obsidian vault

---

# 🧭 Why not rely on AI to link everything?

AI can help _infer_ relationships, but:

- You still need a **canonical registry**
- You need stable URIs
- You need deterministic sync
- You need backups
- You need reproducibility

AI becomes a _helper_, not the foundation.

---

# 🧱 Next Steps (Concrete)

Here’s a clean roadmap:

### **1. Define the registry schema**

SQLite with tables for entities, URIs, metadata, backlinks.

### **2. Build a minimal API**

Local HTTP server with `/search`, `/entity`, `/sync`.

### **3. Build the Google Contacts plugin**

- OAuth
- Fetch contacts
- Map to entities
- Store URIs
- Expose to autocomplete

### **4. Build the Obsidian autocomplete plugin**

- Calls `/search`
- Injects suggestions into `[[ ]]` autocomplete

### **5. Add more plugins**

Google Photos → Strava → GitHub → Instagram → Local FS.

---

# If you want, I can sketch:

- the exact SQLite schema
- the plugin API
- the Obsidian integration
- the URI resolver format
- the sync algorithm
- the deduplication logic
- the backup/export format

Just tell me which piece you want to design next.