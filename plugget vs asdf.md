---
views: 2
last viewed: 2026-02-22
---
[[AI article]]

While **mise** and **asdf-vm** are powerful package managers, they solve a fundamentally different problem than [[Plugget]].

The short answer is: **No, they likely cannot replace Plugget** because they focus on **Developer Runtimes** (Node, Python, Ruby), whereas Plugget focuses on **DCC Plugins** (Maya, Blender, Unreal).

Here is a breakdown of why your project is unique compared to them:

### 1. Scope: Runtimes vs. App-Internal Plugins

- **Mise / [[asdf]]:** These are "Runtime Version Managers." They are designed to manage different versions of programming languages (e.g., "I need Node 18 for Project A and Node 20 for Project B") and CLI tools (like `fzf`, `kubectl`, or `terraform`).
    
- **Plugget:** This is an "Application Plugin Manager." It installs scripts, addons, and tools _into_ a host environment (like Blender’s `scripts/addons` folder or Maya’s modules path). Mise and ASDF have no concept of "Blender Addons" or "Maya Plugins"; they wouldn't know where to put the files or how to register them with the host software.
    

### 2. Targeted Users: Developers vs. Artists/Tech Artists

- **Mise / ASDF:** These are strictly CLI-driven tools for developers. They require shell configuration (`.zshrc`, `.bashrc`) and use shims or PATH manipulation to work.
    
- **Plugget:** You’ve built Plugget specifically for the VFX/Games industry. By providing a **Qt UI** and 1-click installs, you are serving artists who may never open a terminal. Mise and ASDF have no GUI and are not built to be embedded inside a Maya or Blender window.
    

### 3. Cross-Platform Support (Specifically Windows)

- **ASDF:** Primarily built for Unix-like systems (macOS/Linux). Windows support is notoriously difficult and usually requires WSL2.
    
- **Mise:** Written in Rust and has better Windows support than ASDF, but it is still focused on the developer workflow (environment variables, task running).
    
- **Plugget:** Since it's Python-based and interacts with DCCs (which are often Windows-first in many studios), it handles the specific directory structures of Windows creative apps much better.
    

### Comparison Summary

|**Feature**|**Plugget**|**Mise / ASDF**|
|---|---|---|
|**Primary Target**|Plugins for DCCs (Maya, Blender, etc.)|Dev tools (Python, Node, Go, Rust)|
|**Install Target**|App-specific folders (`/addons`, etc.)|System PATH / Shims|
|**UI**|Qt UI (Embedded in DCCs)|CLI Only|
|**Dependency Mgmt**|Handles `pip` deps for specific DCCs|Manages versions of the languages themselves|
|**Audience**|Tech Artists & Animators|Software Engineers & DevOps|

### Could they coexist?

Actually, they complement each other! A developer might use **Mise** to manage the version of **Python** they use to write **Plugget** packages.

**When should you consider moving to Mise/ASDF?**

Only if you decide to pivot Plugget away from being a "Plugin Manager" and toward being a "Toolchain Manager" (e.g., managing which version of the Maya executable or standalone Python a studio uses).

**Verdict:** Keep building **Plugget**. The DCC ecosystem (Maya, Blender, 3ds Max, Unreal) is a "walled garden" that general-purpose package managers like Mise and ASDF don't understand. Your project fills a very specific, high-value niche in the pipeline industry that those tools aren't designed to touch.

---
cant asdf manage installing plugins?

---

You're absolutely right that **asdf** uses a "plugin" architecture, but there is a major distinction in how that word is being used.

In **asdf** (and **mise**), a "plugin" is a script that teaches the manager how to install a specific **language or tool**. In **Plugget**, a "plugin" is the **content** being installed into a creative application.

Here is the breakdown of why they aren't interchangeable:

### 1. The "Plugin" Definition Gap

- **asdf Plugin:** This is a set of scripts (usually hosted in a Git repo) that tells asdf: _"To install Python, go to this URL, download this source, and run these build commands."_ You are installing the **engine**.
    
- **Plugget Package:** This is a tool (like a Maya auto-rigger or a Blender sculpting tool) that needs to be moved into a specific folder so an artist can use it. You are installing the **cargo**.
    

### 2. The Environment Problem

Asdf works by using **shims**. When you type `python` in your terminal, asdf intercepts that command and redirects it to the version you've selected.

DCCs like Maya or Unreal don't look at shims; they have their own internal Python interpreters and hardcoded paths. If you used asdf to "install" a Maya plugin, asdf would put it in its own hidden folder (`~/.asdf/installs/...`), but Maya would have no idea it exists. Plugget's "superpower" is knowing exactly where each specific DCC expects to find its tools.

### 3. Managing Internal Python Dependencies

Many DCC plugins require specific Python libraries (`pip install requests`, etc.).

- **asdf** manages the version of Python itself.
    
- **Plugget** manages the installation of libraries _into_ the specific site-packages of the DCC, or handles the path-appending logic so the DCC can see them without breaking the user's system Python.
    

---

### Comparison of the "Installation Flow"

|**Step**|**asdf / mise**|**Plugget**|
|---|---|---|
|**What is installed?**|A runtime (Python 3.10, Node 18).|A tool (Blender Photogrammetry Addon).|
|**Where does it go?**|A central version-managed directory.|The DCC's specific script/addon folder.|
|**How is it triggered?**|Terminal command or `.tool-versions`.|Python code inside the DCC or a Qt UI.|
|**Registry**|[asdf-plugins repo](https://github.com/asdf-vm/asdf-plugins)|[Plugget-pkgs repo](https://www.google.com/search?q=https://github.com/plugget/plugget-pkgs)|

---

### Could you use asdf to power Plugget?

Technically, you _could_ write an asdf plugin that installs a Blender addon, but it would be like using a freight train to deliver a pizza. Asdf isn't designed to:

1. Detect which version of Blender is currently running.
    
2. Refresh the Blender UI to show the new addon.
    
3. Handle the different "manifest" formats (like `bl_info` in Blender) that you've already automated.
    

**Your project is essentially the "NPM" or "PyPI" for Creative Tools.** Asdf is more like "NVM" or "pyenv." They operate at different levels of the software stack.

Would you like me to look at your `plugget-pkgs` manifest structure to see if there are ways to make it even more robust for different DCCs?