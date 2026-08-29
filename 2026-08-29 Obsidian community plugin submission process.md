---
energy: 5
tags:
- technical
- obsidian
- development
- guides
---

# 📦 Submitting an Obsidian Community Plugin

## 🔄 The New Submission Workflow

Obsidian **deprecated the legacy GitHub Pull Request method** (which previously required creating a PR to `obsidianmd/obsidian-releases/community-plugins.json`). 

All community plugins and themes are now submitted and managed through the official **Obsidian Community Directory Portal**:
🔗 **[community.obsidian.md](https://community.obsidian.md)**

---

## 📋 Repository Prerequisites Checklist

Before submitting, ensure the plugin repository meets the official standards:

1. **Public GitHub Repository:**
   - Must contain a valid `manifest.json`, `package.json`, and `README.md`.
   - Open-source `LICENSE` (e.g., MIT, Apache 2.0).
2. **GitHub Release Assets:**
   - A published GitHub Release with a tag matching `manifest.json` version (e.g., `1.0.0`).
   - Attached release assets must include:
     - `manifest.json`
     - `main.js` (bundled executable)
     - `styles.css` (even if empty or minimal styling)
3. **Manifest Specs:**
   - Unique `id` across all community plugins.
   - Correct `name`, `author`, `version`, and `minAppVersion`.
   - Clean `description` (concise summary of functionality).

---

## 🚀 Step-by-Step Submission Instructions

1. Navigate to **[community.obsidian.md](https://community.obsidian.md)**.
2. Sign in with your Obsidian account (and authorize GitHub connection).
3. Click **"New plugin"** in the sidebar / dashboard.
4. Paste your public GitHub repository URL:
   ```text
   https://github.com/<username>/<repo-name>
   ```
5. Click **Submit**.

---

## 🔍 Review & Automated Release Lifecycle

* **Initial Review:** The automated directory validator checks manifest consistency and release assets, then queues the submission for manual review by the Obsidian team.
* **Automated Future Updates:** Once approved, you **never** need to submit the form again. Obsidian's backend automatically syncs updates whenever a new GitHub Release tag is published.
* **Analytics & Management:** You can claim ownership and monitor install metrics directly on `community.obsidian.md`.

---

## 🔗 Related Notes
- [[Obsidian plugins in use]]
- [[2026-08-29 Obsidian lazy loading plugins compared]]
- [[Obsidian faster startup]]
- [[Obsidian plugin startup optimization]]
