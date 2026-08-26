---
date: 2026-08-24
tags:
  - technical
  - obsidian
  - performance
  - pkm
origin-sha: e14817ef
created: 2026-08-24
---

Why [[Obsidian]] search and indexing slows down on large vaults (5,000–10,000+ notes) and how to restore sub-100ms instant search.

## Current Vault Audit & Implementation Status

Audit recommendations for vault performance:

| Optimization Suggestion | Status in Vault | Action Taken / Recommendation |
| :--- | :---: | :--- |
| **`userIgnoreFilters` in `app.json`** | 🟢 **Implemented** | Add `**/.git/**`, `**/.smart-env/**`, `.trash/**`, and `**/node_modules/**` so file watchers skip hidden binary churn. |
| **Plugin Startup Delaying** | 🟢 **Implemented** | Delay non-essential startup plugins using [[obsidian-plugin-groups]] per [[Obsidian faster startup]]. |
| **Heavy Vector Plugins** | 🟢 **Deferred** | Keep heavy client-side vector indexers disabled on startup to prevent UI thread freezing. |
| **Workspace Open Tabs** | 🟢 **Cleaned** | Keep open tab count minimal to eliminate DOM hydration freeze. |
| **Windows Defender Exclusion** | 🟢 **Implemented** | Exclude vault folder and Obsidian executable per [[Obsidian Windows Defender exclusion]]. |

---

## Why It Slows Down at 5,000+ Notes

Pure Markdown text parsing in Obsidian is lightweight (5k notes ≈ 20–50 MB text, which Electron can index in memory in under 2 seconds). When search or indexing crawls or freezes the UI, it is almost always caused by one of five bottlenecks:

1. **Unexcluded Hidden & Binary Folders:** Obsidian's file watcher trying to scan `.git/objects`, submodules, `.smart-env`, `.trash`, or attachment directories.
2. **Heavy Indexing Plugins on Main Thread:** Plugins like **Omnisearch**, **Smart Connections**, or **Dataview** building vector/BM25 indexes on the main JavaScript event loop instead of a background worker.
3. **Windows Defender / Antivirus Scanning:** Real-time protection intercepting thousands of small file reads during initial vault indexing.
4. **Unscoped Dataview Queries:** Live `dataview` or `query` blocks running across the entire vault on every keystroke.
5. **Corrupted Metadata Cache:** Fragmented local cache causing Obsidian to repeatedly drop and rebuild its index.

---

## Step-by-step Fixes

### Add Folder Exclusions in Obsidian Settings
Tell Obsidian to completely ignore heavy, non-note folders from search, graph, and file watchers:
- Go to **Settings -> Files and links -> Excluded files**.
- Add the following patterns:
  - `**/.git/**`
  - `**/.smart-env/**`
  - `**/node_modules/**`
  - `_scripts/**`
  - `.trash/**`

### Exclude Vault from Windows Defender
Windows real-time antivirus scans every file read during indexing, slowing searches by 5–10x. Follow [[Obsidian Windows Defender exclusion]] to add folder and process exclusions.

### Scope Dataview Queries
Never query the root vault without a folder or tag filter:
- ❌ Slow: `TABLE file.mtime WHERE ...`
- ✅ Fast: `TABLE file.mtime FROM "projects"` or `FROM #project`

### Optimize Full-text Search Plugins
If using **Omnisearch** or **Smart Connections**:
- **Omnisearch Settings:** Enable *"Index in background worker"* and disable *"Index PDF files"* / *"Index images"* if not needed.
- **Cache Vector Models:** If using embeddings, follow [[offline GPU embeddings with incremental cache]] to avoid running model inference on the UI thread.

### Clear Corrupted Index Cache
If indexing remains stuck or shows a black screen:
1. Close Obsidian.
2. Navigate to your vault folder: `.obsidian/`.
3. Delete or rename the cache databases: `workspace.json` and the `Cache/` folder.
4. Re-open Obsidian to force a clean, unfragmented re-index.

---

## External Alternative: Lightning-fast CLI Search

For instant full-vault searching across 10,000+ notes without opening Obsidian search:
- **Ripgrep (`rg`):** Searches entire vault in **< 10 ms**:
  ```bash
  rg -i "search query" /path/to/vault
  ```
- **FZF File Jump:** Instant fuzzy filename searching:
  ```bash
  fzf --walker-root=/path/to/vault
  ```

---

## References
- [[pkm metadata indexer]] — standalone SQLite FTS5 + neural embedding indexer with resident daemon (`searchd.py`).
- [[vault hybrid search]]
- [[lightning-fast unified search plugin for obsidian]]
- [[Obsidian Windows Defender exclusion]]
- [[Obsidian faster startup]]
- [[Obsidian plugins in use]]
