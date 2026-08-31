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

### 1. Create URI converter wrapper with vault detection
Create `~/.local/bin/obsidian-open` to convert markdown paths. If the note is inside an Obsidian vault, it opens in Obsidian via URL-encoded `obsidian://open?vault=...&file=...`. If the file is outside any vault (e.g. standalone repo README or temp file), it falls back to the system text editor (`gnome-text-editor` / `$EDITOR`):

```python
#!/usr/bin/env python3
import sys, os, json, shutil, urllib.parse, subprocess
from pathlib import Path

def get_vaults():
    config_paths = [
        Path.home() / ".var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json",
        Path.home() / ".config/obsidian/obsidian.json"
    ]
    for config_path in config_paths:
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                return data.get("vaults", {})
            except Exception:
                pass
    return {}

def find_vault_root(file_path: Path):
    curr = file_path.parent if file_path.is_file() else file_path
    for p in [curr, *curr.parents]:
        if (p / ".obsidian").is_dir():
            return p, p.name

    vaults = get_vaults()
    for vid, vinfo in vaults.items():
        vpath_str = vinfo.get("path", "")
        if vpath_str:
            vpath = Path(vpath_str).resolve()
            try:
                file_path.relative_to(vpath)
                return vpath, vpath.name
            except ValueError:
                continue
    return None

def open_with_fallback(file_path: Path):
    for ed in [os.environ.get("VISUAL"), os.environ.get("EDITOR"), "gnome-text-editor", "code", "gedit", "nano"]:
        if ed and shutil.which(ed):
            subprocess.run([ed, str(file_path)])
            return
    subprocess.run(["gio", "open", str(file_path)])

def open_target(target: str):
    if not target:
        return
    if target.startswith("obsidian://"):
        subprocess.run(["flatpak", "run", "md.obsidian.Obsidian", target])
        return
    
    if target.startswith("file://"):
        url_obj = urllib.parse.urlparse(target)
        raw_path = urllib.parse.unquote(url_obj.path)
    else:
        raw_path = target
    
    file_path = Path(raw_path).resolve()
    if not file_path.exists():
        encoded_path = urllib.parse.quote(str(file_path), safe="/:")
        subprocess.run(["flatpak", "run", "md.obsidian.Obsidian", f"obsidian://open?path={encoded_path}"])
        return

    vault_info = find_vault_root(file_path)
    if vault_info:
        vault_root, vault_name = vault_info
        rel = file_path.relative_to(vault_root)
        encoded_file = urllib.parse.quote(str(rel), safe="/")
        encoded_vault = urllib.parse.quote(vault_name)
        uri = f"obsidian://open?vault={encoded_vault}&file={encoded_file}"
        subprocess.run(["flatpak", "run", "md.obsidian.Obsidian", uri])
    else:
        open_with_fallback(file_path)

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
