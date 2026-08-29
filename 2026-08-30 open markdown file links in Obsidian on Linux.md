---
created: 2026-08-30
tags:
- technical
- linux
- obsidian
- cli
- fedora
aliases:
- open markdown file links in Obsidian on Linux
- obsidian terminal link opener
- click markdown links to open in obsidian
---

How to configure Linux (GNOME / Flatpak) so clicking `file:///path/to/note.md` in your terminal or agent console opens the note directly inside [[Obsidian]].

Related: [[public/idea - clickable obsidian links in agent console|clickable obsidian links in agent console]], [[2026-08-29 new Linux PC setup log]]

## Problem
Terminals and AI consoles (like [[public/how to inspect antigravity cli sessions|Antigravity CLI]] or VS Code) render `file:///` URLs as clickable links. When clicked, Linux queries `xdg-open` / `gio` for the `text/markdown` MIME handler, which defaults to a text editor (like GNOME Text Editor) rather than Obsidian.

Obsidian Flatpak expects `obsidian://open?path=...` URIs rather than raw filesystem paths passed via CLI.

## Setup

### 1. Create URI converter wrapper
Create `~/.local/bin/obsidian-open` to convert raw file paths and `file://` URLs to URL-encoded `obsidian://` protocol calls:

```python
#!/usr/bin/env python3
import sys, os, urllib.parse, subprocess

def open_target(target):
    if not target:
        return
    if target.startswith("obsidian://"):
        subprocess.run(["flatpak", "run", "md.obsidian.Obsidian", target])
        return
    if target.startswith("file://"):
        path = urllib.parse.unquote(urllib.parse.urlparse(target).path)
    else:
        path = os.path.abspath(target)
    
    encoded = urllib.parse.quote(path, safe="/:")
    subprocess.run(["flatpak", "run", "md.obsidian.Obsidian", f"obsidian://open?path={encoded}"])

if __name__ == "__main__":
    if len(sys.argv) == 1:
        subprocess.run(["flatpak", "run", "md.obsidian.Obsidian"])
    else:
        for arg in sys.argv[1:]:
            open_target(arg)
```

Make it executable:
```bash
chmod +x ~/.local/bin/obsidian-open
```

### 2. Register desktop entry
Create `~/.local/share/applications/obsidian-markdown.desktop`:

```ini
[Desktop Entry]
Name=Obsidian Markdown
Comment=Open Markdown notes in Obsidian
Exec=/home/hannes/.local/bin/obsidian-open %U
Terminal=false
Type=Application
Icon=md.obsidian.Obsidian
MimeType=text/markdown;text/x-markdown;
StartupWMClass=md.obsidian.Obsidian
Categories=Office;
```

Update desktop database:
```bash
update-desktop-database ~/.local/share/applications
```

### 3. Set default MIME handler
Associate `text/markdown` and `text/x-markdown` with the custom launcher:

```bash
xdg-mime default obsidian-markdown.desktop text/markdown
xdg-mime default obsidian-markdown.desktop text/x-markdown
gio mime text/markdown obsidian-markdown.desktop
gio mime text/x-markdown obsidian-markdown.desktop
```

Clicking any `file:///.../note.md` link in terminal now routes through `obsidian-open` and reveals the note in Obsidian.
