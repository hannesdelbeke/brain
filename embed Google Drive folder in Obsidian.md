---
sentiment:
- 5
sentiment-hash: 50f10761
sentiment-label:
- factual
tags:
- technical
- planning
- work
---

If I download my [[Google Drive]] folder in my vault, i can [[wikilink GDrive files]] in my notes.

## challenges
- potential clashing file names with public notes
	- I expect this is rare since there are no [[Markdown]] files in my drive.
	- If it happens I can just rename the file.
- renaming files in google drive , will break [[wikilink|wikilinks]] in [[my vault]] in [[Obsidian]]
	- renaming likely happens at the start of a file's life. once a file is linked in a note, it's not likely to be renamed. so i don't expect this to often be an issue, if it breaks, i can manually fix it.

### Walkthrough: How to embed GDrive folder on Windows
- Download Google Drive Desktop.
- Launch and sign in.
- Set sync mode to `Mirror files` pointing to `C:\repos\pkm\google-drive` (or keep stream mode).
- Configure `.gitignore` so Git ignores heavy binary assets while tracking `.gsheet` / `.gdoc` shortcuts.

### Walkthrough: How to embed GDrive folder on Linux

On Linux without native Google Drive Desktop, use **Rclone FUSE Mount** to stream or mirror Google Drive into `~/repos/pkm/google-drive`:

1. **Install Rclone:**
   Installed to `~/.local/bin/rclone`.
2. **Authenticate Google Drive (`rclone config`):**
   - Create new remote `gdrive` $\rightarrow$ choose `drive` (Google Drive) $\rightarrow$ follow browser OAuth login.
3. **Mount Google Drive to Vault:**
   Run `scripts/setup_gdrive_linux.sh` or create a systemd user service (`~/.config/systemd/user/rclone-gdrive.service`):
   ```bash
   rclone mount gdrive: ~/repos/pkm/google-drive \
       --vfs-cache-mode full \
       --vfs-cache-max-size 10G \
       --drive-export-formats link.html
   ```
4. **Auto-Mount on Login:**
   ```bash
   systemctl --user enable --now rclone-gdrive.service
   ```
5. **Obsidian Configuration:**
   Enable `"showUnsupportedFiles": true` in `.obsidian/app.json` so Obsidian detects Google Drive files and wikilinks.

---

### Alternative: GNOME Online Accounts
In GNOME Settings $\rightarrow$ Online Accounts, sign into Google. GNOME automatically mounts Google Drive under `/run/user/1000/gvfs/`. Symlink that directory to `~/repos/pkm/google-drive`.

## Linux Failure Modes & Troubleshooting

> [!BUG]- rclone config fails with "Failed to read line: EOF"
> Running interactive `rclone config` in scripted or non-TTY terminals fails with `CRITICAL: Failed to read line: EOF`.
> **Fix:** Use non-interactive direct command `rclone config create gdrive drive scope drive` which opens the default browser directly for OAuth without terminal prompts.

> [!BUG]- google-drive folder remains empty after browser login
> Authorizing Google Drive in the browser only writes credentials to `~/.config/rclone/rclone.conf`. The mount is not active until the systemd service is started.
> **Fix:** Start and enable the mount service:
> ```bash
> systemctl --user enable --now rclone-gdrive.service
> ```

> [!WARNING]- google-drive folder hidden in Obsidian File Explorer
> If `google-drive/` is listed in `.obsidian/app.json` under `"userIgnoreFilters"`, Obsidian will hide the entire folder from the left sidebar file tree.
> **Fix:** Remove `google-drive/` from `userIgnoreFilters` in Obsidian settings (Files and links $\rightarrow$ Excluded files) if you want the folder visible in the sidebar.

> [!WARNING]- git status freezes or leaves index.lock on FUSE mounts
> Using recursive whitelist rules like `!google-drive/**/*.gsheet` in `.gitignore` forces `git status` to traverse the remote FUSE mount over the internet, causing long freezes and lockfile contention.
> **Fix:** Ignore `google-drive/` completely in `.gitignore`, and track local `.gsheet` JSON stubs in the vault root or subfolders.

---

## Past Windows Issues

> [!BUG]- convert to jpg plugin deletes drive files
> The [[Obsidian paste img png to jpg]] plugin causes issues with gdrive syncing.
> The plugin is designed to convert a newly pasted jpg. It seems to do this by detecting new images, renaming and converting to jpg, and then moving the image.
> Moving an image out of drive deletes is from drive.
> And the images were being submitted to git by [[Obsidian plugin - Git]].
> 
> Things seem better after tweaking the settings of the [[Obsidian paste img png to jpg]] plugin
> - disable rename
> - disable move
> 
> I still got some weird bugs though.
> Uncaught (in promise) Error: ENOENT: no such file or directory, rename 
> C:\repos\pkm\google-drive\admin\work\archive\2016 Freejam\robocraft\robocraft wallpapers\ScreensRhino-4.jpg' ->
> 'C:\repos\pkm\google-drive\admin\work\archive\2016 Freejam\robocraft\robocraft wallpapers**NaNimage**\ScreensRhino-4.jpeg'

> [!warning]- slow autocomplete
> After integrating drive in [[my vault]], the [[Obsidian autocomplete]] is terribly slow. (5 seconds). I also rebuild the cache as a test, which might have slowed things.
> However, after fixing the previous image bugs and restarting it seems fine again.

this might be an option

- `xslx` files can be edited in [[google drive]], so could use that instead of gsheet if i want to not be stuck in their custom file format.
- same for `docx` for word docs.

see [[keep using google drive for my sheets in my vault]]
