check out project https://github.com/decaf-dev/obsidian-view-count seems to atm development is dropped and it's archived on github.
use `gh` cli
first check all forks, and summarize what changes they did in each fork. write the summary here:

- **`Moyf/obsidian-view-count`** (19 commits ahead; active maintained fork):
  - **View Date Tracking**: Added support for tracking and frontmatter auto-syncing `viewed_at` date alongside view count.
  - **Frontmatter Sync Safety & Batch Modals**: Replaced destructive frontmatter auto-sync (which previously applied today's date or deleted frontmatter across all notes unexpectedly) with explicit confirmation modals (`ConfirmModal`) and cache helpers (`writeViewCountFromCache`, `writeViewDateFromCache`).
  - **Required Properties Filter**: Added setting to skip frontmatter sync unless a note contains specific comma-separated YAML properties.
  - **Recent View Panel & Search**: Revamped panel with a Recent tab, time-grouped sections (*Today*, *Yesterday*, *Within 3 days*, *Earlier*), and highlighted search match text.
  - **Native Obsidian UI Menus**: Replaced platform-native legacy dropdown menus with native Obsidian `Menu` controls.
  - **i18n & Modern Toolchain**: Added `zh-CN` / `en` localization; upgraded to TypeScript 5.9, ESLint 8.58, esbuild 0.28, Svelte 5, and Svelte-preprocess 6.
  - **Local Vault Dev**: Added `.env` support (`OBSIDIAN_VAULT_PATH`) for local testing.

- **`gkwa/obsidian-view-count`** (6 commits ahead):
  - Fixed Obsidian API `moment` TypeScript type errors using `(moment as any)`.
  - Added `skipLibCheck: true` and excluded `node_modules` in `tsconfig.json`.
- **`ruri-afk/obsidian-view-count`**, **`gkwa/obsidian-view-count-1`**, **`taylormonacelli/obsidian-view-count`**:
  - No new commits ahead of upstream master.

investigate https://github.com/tahayigitmelek/note-radar
what's the difference how it tracks viewcount?

- **Data Storage**:
  - **Note Radar**: Stores view stats (`viewCount`, `firstViewedAt`, `lastViewedAt`) **strictly in plugin storage (`data.json`)**. It does NOT alter or touch the markdown note files' frontmatter/YAML.
  - **Obsidian View Count**: Stores stats in `data.json` AND can **write/sync `views` and `viewed_at` directly into note YAML frontmatter**.

- **User Interface & Analytics**:
  - **Note Radar**: Offers a dedicated full-tab analytics dashboard view (Svelte table) featuring column sorting (name, total views, last viewed, time since last view), JSON data export, reset capabilities, and tracking of both viewed and unviewed vault notes.
  - **Obsidian View Count**: Focuses on sidebar view count / recent panels, status bar counts, note header display, and metadata sync.

are there other things worth mentioning?
- **File Renaming Support**: In `obsidian-view-count`, frontmatter property sync (`views`, `viewed_at`) automatically travels with notes when moved or renamed. In addition, Moyf's fork added validation (`countValidEntries`) so cached path data doesn't corrupt moved/renamed notes.
- **Recommended Maintenance Fork**: `Moyf/obsidian-view-count` is effectively the active continuation of the archived `decaf-dev` repository, bringing current Obsidian API & Svelte 5 compatibility.

i don't want to use frontmatter. [[2026-07-22 follow up Obsidian viewcount|it causes issues]].
assuming no frontmatter. do either have renaming support.
- **`obsidian-view-count`**: **YES**. It registers a `vault.on('rename')` event listener. When a note is renamed or moved to another folder, `cache.renameEntry(file.path, oldPath)` automatically updates the internal path key in `data.json`. View history is fully preserved without ever modifying note frontmatter or source files.
- **`note-radar`**: **NO**. It only listens to workspace `file-open` events and does not handle `rename` events. Renaming a note leaves the old path as an orphaned entry in `data.json`, and opening the renamed note creates a fresh entry with a view count of 1.

install [Moyf/obsidian-view-count](https://github.com/Moyf/obsidian-view-count) in this vault.

draft for later, dont do this now:
- [x] fork the repo, and ask me which changes are worth bringing over.
	will continue from https://github.com/Moyf/obsidian-view-count
- [x] then ensure see if there is support for renaming files. 
