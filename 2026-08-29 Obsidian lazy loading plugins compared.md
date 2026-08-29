---
energy: 5
tags:
- technical
- obsidian
- performance
- pkm
---

# ⚡ Obsidian Lazy Loading Plugins Compared

## 🧠 How Plugin Loading Works in Obsidian

By default, Obsidian initializes all active community plugins **synchronously and sequentially** in the exact array order defined in `.obsidian/community-plugins.json` during the boot sequence before the workspace layout is fully hydrated.

As a vault grows in complexity and plugin count, eager initialization of heavy indexers, background watchers, and complex UI integrations can introduce noticeable launch latency.

Lazy loading addresses this by altering when and how plugins initialize:
1. **Time-Delayed Loading:** The core workspace renders immediately, and non-essential plugins are initialized in the background after a configured delay (e.g., 2–10 seconds).
2. **On-Demand (Proxy) Loading:** Plugins remain completely dormant at 0ms startup cost until their registered commands, ribbon buttons, or custom view types are explicitly invoked.
3. **Platform/Device Conditional Loading:** Heavy indexing plugins are enabled on Desktop while kept disabled on Mobile/Tablet devices.

---

## 🔍 Top Lazy Loading Plugins Compared

| Plugin | Mechanism | Granularity | Best Use Case |
| :--- | :--- | :--- | :--- |
| **[[Plugin Groups]]** (`obsidian-plugin-groups`) | Group-based delay timers & manual toggle switches | Group | Grouping plugins by workflow or context (e.g., Writing, Development) |
| **[[Lazy Plugin Loader]]** (`lazy-plugins`) | Direct millisecond delay per plugin | Per-plugin | Fine-grained, independent timer delays (e.g. +3s, +5s) |
| **[[On-Demand Plugins]]** (`on-demand-plugins`) | Command palette & view proxy | Action / View | Tools only used occasionally via hotkeys or commands |
| **[[Control Center]]** (`plugins-control`) | Device detection (Mobile vs Desktop) + delay timers | Platform / Device | Multi-device setups where mobile needs to remain lean |

---

## 🛠️ Detailed Breakdown of Each Tool

### 1. [[Plugin Groups]] (`obsidian-plugin-groups`)
* **Author:** MProjects
* **Mechanism:** Allows organizing plugins into named groups. An entire group can be assigned a startup delay timer (e.g., 3s) or manually toggled on/off in batch.
* **Pros:**
  * Great for high-level organization and context switching (e.g., a "Distraction-Free" profile with extra toolbars disabled).
  * Batch enabling/disabling of related toolsets.
* **Cons:**
  * Requires manual group creation and assignment; less direct if you just want to add a quick delay to a single plugin.

### 2. [[Lazy Plugin Loader]] (`lazy-plugins`)
* **Author:** Alan Grainger
* **Mechanism:** Adds a delay configuration column directly to your installed plugins list.
* **Pros:**
  * Lightweight and zero setup beyond entering millisecond values (e.g., `5000ms` for Git sync).
  * Direct per-plugin control without maintaining groups.
* **Cons:**
  * Fixed timers only; does not dynamically load on command.

### 3. [[On-Demand Plugins]] (`on-demand-plugins`)
* **Author:** mavam
* **Mechanism:** Proxies plugin commands and view registrations while keeping the plugin bundles unloaded. When a command is triggered from the command palette or hotkey, the plugin is loaded dynamically on the fly.
* **Pros:**
  * **True 0ms startup impact** for single-purpose utilities (e.g., Excalidraw, Importers, Code Viewers, Pandoc).
  * Fully transparent user experience during daily note-taking.
* **Cons:**
  * Unsuitable for background indexing plugins (like Dataview or Git) that need to monitor file modifications continuously.

### 4. [[Control Center]] (`plugins-control`)
* **Author:** polyipseity
* **Mechanism:** Platform-specific rules (Desktop vs Phone vs Tablet), combined with delayed activation.
* **Pros:**
  * Essential for cross-device vaults where heavy desktop plugins would otherwise slow down mobile launch times.
* **Cons:**
  * More complex settings interface.

---

## 🎯 General Plugin Categorization Strategy

When auditing plugins for startup optimization, categorize them into three buckets:

### 🟢 1. Immediate Startup (0s Delay)
* **Core Workspace Enhancers:** Homepage loaders, UI layout stabilizers, and theme/icon managers where delayed loading would cause visual pop-in or layout shifts.
* **Immediate Indexers (if on homepage):** Dataview or tasks plugins if your landing page contains live query tables.

### 🟡 2. Timer Delay Candidates (3s – 10s Delay)
* **Background Sync & File Watchers:** Automated Git sync, backup tools, or auxiliary metadata indexers that do not require immediate interactivity in the first second of launching.
* **Secondary UI helpers:** Backlink collapsers, property managers, or formatting clean-up tools.

### 🔵 3. On-Demand Candidates (Command/Action Triggered)
* **Single-Purpose Utility Tools:** Importers/exporters, code viewers, visual sketch tools, or specialized conversion utilities that are only executed occasionally.

---

## 🔗 Related Notes
- [[Obsidian plugin startup optimization]]
- [[Obsidian plugins in use]]
- [[Obsidian faster startup]]
