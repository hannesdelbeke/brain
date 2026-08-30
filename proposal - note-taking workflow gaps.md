---
date: 2026-08-30
created: 2026-08-30
tags:
  - obsidian
  - pkm
  - plugins
  - proposal
---

Thirteen small, independent note-capture/browsing/publishing UX ideas from the vault, checked one by one against the existing Obsidian plugin ecosystem before considering a custom build. Six already have an off-the-shelf plugin. Seven need custom work (two of those aren't really plugin requests at all — one is a workflow already adopted, one is a personal reflection).

## Checklist

- [x] **Auto-titling / no-friction capture** — [[random title note flow]]. Ask: create a note instantly, let AI fill in the title later. Found: [auto-title](https://github.com/dpshde/auto-title) (Ollama or OpenAI, renames on content change), [Title Generator](https://community.obsidian.md/plugins/title-generator) (OpenAI GPT, command palette/right-click), [smart-note-namer](https://github.com/bkindler/smart-note-namer) (Claude Haiku, date-prefix + title + tags, ~$0.001/note). Install any of the three from Community Plugins (or via BRAT for the GitHub-only ones) and point it at an API key.

- [x] **Fuzzy search** — [[notes fuzzy search]]. Ask: fuzzy/typo-tolerant search better than the built-in quick switcher. Found: [Omnisearch](https://community.obsidian.md/plugins/omnisearch) — BM25-ranked, typo-tolerant, indexes PDFs/images, has a Firefox companion extension. Install from Community Plugins, done.

- [x] **Auto-add aliases from wikilinks** — [[auto add obsidian aliases]]. Ask: `[[note|alias]]` should auto-register `alias` on `note`'s frontmatter. Found: [obsidian-note-aliases](https://github.com/pulsovi/obsidian-note-aliases) by pulsovi — cursor on a piped wikilink, run the command, it adds the alias to the target note's YAML. Also relevant: [Alias from heading](https://www.obsidianstats.com/plugins/obsidian-alias-from-heading) (reverse direction) and [Link Plus](https://community.obsidian.md/plugins/link-plus) (broader alias dashboard). Install obsidian-note-aliases via BRAT (not in community list last checked) or Community Plugins if listed.

- [x] **Sliding panes** — [[sliding panes]]. Ask: Andy-Matuschak-style stacked panes instead of shrinking splits. Found: [Sliding Panes (Andy Matuschak Mode)](https://github.com/deathau/sliding-panes-obsidian) by deathau — already the plugin the source note points at; confirmed it's a real, actively-discussed community plugin, not just a CSS snippet. The browser-extension half of the idea (sliding panes for Chrome tabs) has no equivalent — no hit for a Chrome extension doing this.

- [x] **Public notes / tiered sharing** — [[public notes]]. Ask: publish some notes publicly, share others with just one person (a tier between public and private). Found: [Share Note](https://github.com/alangrainger/share-note) — end-to-end encrypted single-note sharing via link, exactly the "share with one person" tier the note asks for (its TODO: "create a setup with more layers than public or private"). For the fully-public tier, see the Digital Garden entry below. [Share Hosted](https://community.obsidian.md/plugins/share-hosted) is a newer alternative with revocable/expiring links.

- [x] **Share TA notes with the world / digital garden publishing** — [[share TA notes with world]]. Ask: publish a wiki of notes to the public. Found: [Digital Garden](https://github.com/oleeskild/obsidian-digital-garden) plugin (`dg-publish: true` frontmatter flag, pushes to a GitHub-hosted site) or [Quartz](https://quartz.jzhao.xyz/) (static site generator, symlink the vault in, filter by `publish: true`). Both are mature, widely used, free alternatives to Obsidian Publish.

- [ ] **Discover a garden's essence** — [[discover a garden's essence]]. Ask: help a visitor find an author's core/most-popular notes in a big digital garden, not just wander the graph. No dedicated "popular pages" plugin found for Obsidian or Digital Garden/Quartz — the practical answer found is bolting on ordinary web analytics (Plausible/Umami/GA) to the published Quartz/Digital-Garden site and building a manual "popular" page from that data, which is exactly what the source note's `nesslabs.com` example does. Obsidian's built-in graph view covers the "see the biggest nodes" angle natively already. No existing plugin found, needs custom build (or a manually-curated `[[most popular]]` note, which the source note already gestures at).

- [ ] **Infinite scroll for notes** — [[infinite scroll for notes]]. Ask: a swipeable, TikTok-style infinite feed of interesting notes. No plugin implements a literal swipe/feed UI. Closest existing tools: [Serendipity](https://community.obsidian.md/plugins/serendipity) (shows a random note in a modal on vault open) and [Smart Random Note](https://github.com/erichalldev/obsidian-smart-random-note)/[Random Note Picker](https://community.obsidian.md/plugins/random-note-picker) (command-driven random note, filterable by folder/tag/date range). None give the card-swipe/momentum-scroll feel the note describes. No existing plugin found, needs custom build.

- [ ] **Reducing note folders** — [[reducing note folders]]. Not actually a plugin ask — it's a workflow already adopted (single inbox folder + linking over categorizing, per [[minimal notetaking]]). No plugin needed.

- [ ] **Drag-drop extract to new note** — [[drag drop extract to new note]]. Ask: select text, drag onto a folder to spawn a new note from it (or onto a note to append). No plugin does this exact interaction. Closest: [Text Transporter](https://github.com/TfTHacker/obsidian42-text-transporter) (commands to move/extract text into notes, no drag-and-drop) — there's an [open GitHub issue](https://github.com/TfTHacker/obsidian42-text-transporter/issues/82) requesting exactly this drag-and-drop UX, unresolved. No existing plugin found, needs custom build.

- [ ] **Delete tab UX inconsistent with close tab** — [[obsidian - delete tab ux different from close tab]]. Ask: deleting a note should be undoable via `Ctrl+Shift+T` like closing a tab is. This is core Obsidian tab behavior, not a plugin surface — confirmed via a [forum feature-request thread](https://forum.obsidian.md/t/please-undo-deleting-a-file-now-closes-its-tab/55143) (and a related [undo-deletion request](https://forum.obsidian.md/t/undo-deletion-of-note/9067)) that this is a known, still-open gap with no plugin fix. No existing plugin found, needs a core Obsidian fix (file an upvote on the forum thread rather than build).

- [ ] **PKM social media / federated gardens** — [[PKM social media]]. Ask: subscribe to other people's PKM/digital gardens, get notified of new notes and backlinks across sites, Substack-style. No federated/webmention/ActivityPub-style subscription plugin found for Obsidian — publishing plugins (Digital Garden, Quartz) only cover the one-way vault-to-website step, nothing covers cross-site following or backlink notifications. No existing plugin found, needs custom build (would likely mean RSS feeds off published Quartz/Digital Garden sites plus a webmention-style receiver, per IndieWeb tooling — not evaluated in depth here).

- [ ] **Pros/cons of saving AI output** — [[pros cons of saving ai output]]. Not a plugin ask — it's a personal decision-framework note (save the prompt vs. save the answer). No plugin needed.

## Tally

- Off-the-shelf plugin found: 6 — auto-titling, fuzzy search, auto-aliasing, sliding panes, public/tiered notes, digital-garden publishing.
- Needs custom work / no exact plugin: 7 — discover-a-garden's-essence, infinite scroll, reducing folders (not a plugin ask), drag-drop extract, delete-tab UX (core app gap), PKM social media, AI-output pros/cons (not a plugin ask).
