---
views: 3
---
Setting up **[Backlog.md](https://github.com/MrLesk/Backlog.md)** inside an [[Obsidian vault]] is straightforward because both tools are built around local [[Markdown]] files.

---

## 1. Installation

First, install Backlog.md globally on your machine using your terminal:

Bash

```
npm i -g backlog.md
# or using bun / brew:
# bun add -g backlog.md
# brew install backlog-md
```

---

## 2. Initialize in Your Obsidian Vault

Open your terminal, navigate to your Obsidian vault folder, and run the initialization command:

Bash

```
# Navigate to your vault folder
cd /path/to/your/ObsidianVault

# Initialize Backlog.md
backlog init "My Vault Tasks"
```

> **Note:** If your vault is **not** a Git repository, add the `--no-git` flag:
> 
> Bash
> 
> ```
> backlog init "My Vault Tasks" --no-git
> ```

---

## 3. Configure Output Folder for Obsidian

During the interactive `backlog init` wizard (or by editing `backlog.config.yml`), you can choose where Backlog stores its task files.

By default, it creates a `backlog/` folder in your vault. Because these are standard Markdown files (`.md`), **Obsidian will automatically index them as notes**.

---

## 4. How to Use It Day-to-Day

### Option A: From the Terminal or Web Board

- **CLI:** Create and manage tasks using simple terminal commands:
    
    Bash
    
    ```
    backlog task create "Review monthly goals" --ac "Write summary; Clean inbox"
    ```
    
- **Browser UI:** Run `backlog browser` in your terminal to launch a local drag-and-drop Kanban board in your browser. Any changes you make sync instantly back to the Markdown files in your vault.
    

### Option B: Inside Obsidian Directly

- **Community Plugin:** Install the community plugin **[vscode-backlog-md](https://github.com/ysamlan/vscode-backlog-md)** or search for Backlog integrations in Obsidian to render and interact with your task board directly inside your editor.
    
- **Direct Editing:** Since tasks are just `.md` files, you can open, link to, or tag any task file inside Obsidian like a regular note.
    

---

## 5. Working with AI Agents (Optional)

If you use AI assistants (such as Claude Code, Codex, or Gemini CLI) alongside your Obsidian vault:

1. Direct your AI tool to the vault folder.
    
2. Tell it to run `backlog instructions overview` to understand your workflow.
    
3. Ask the AI to write specs, plans, or structure your project tasks directly inside your vault!