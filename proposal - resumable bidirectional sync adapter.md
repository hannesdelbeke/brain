---
date: 2026-08-30
created: 2026-08-30
tags:
  - technical
  - planning
  - sync
  - pkm
aliases:
  - resumable bidirectional sync adapter
  - sync adapter pattern
---

Every third-party sync integration tried for this vault — [[2025-11-25 keepsidian issues|Keepsidian]], [[Glasp review|Glasp]], [[Hypothesis review|Hypothesis]], [[Github markdown to site|GitHub-to-site publishing]], [[export goodreads to obsidian|Goodreads]], [[obsidian-strava-sync|Strava]] — fails the same handful of ways. None of the failures are integration-specific; they are the same three missing pieces of generic sync engineering, rebuilt badly or not at all, in six unrelated plugins.

## the common failure shape

1. **One-directional only.** Source → vault, never vault → source. The old [[Hypothesis review|obsidian-hypothesis-plugin]] only pulled from the Activity Page; the Goodreads RSS route only reads; [[2025-11-25 keepsidian issues|Keepsidian]]'s original mode only imported.
2. **Create-only, no upsert.** The sync writes a new note if none exists and silently does nothing (or errors) if one does, instead of checking whether the remote record changed and updating in place. [[obsidian-strava-sync|obsidian-strava-sync]]'s importer calls `vault.create()` and swallows "file already exists" rather than diffing and updating — so an edited Strava title or description never reaches the vault after the first import.
3. **Paginated/rate-limited fetch with no resume state beyond a single watermark.** [[obsidian-strava-sync|obsidian-strava-sync]] hardcodes `PER_PAGE = 30` and never requests page 2, so "sync everything" silently truncates at ~30 activities / ~21 days. Goodreads' RSS feed caps at 100 items per shelf, with no cursor at all past that. Old Glasp had no incremental fetch — only "download 1 note" or "download all," burning bandwidth every time.
4. **Deletion is unrepresented.** [[2025-11-25 keepsidian issues|Keepsidian]] can't propagate a delete back to Google Keep; nothing in this list handles the "record removed at source" case as anything other than an orphaned note.

Each of the plugins above solved at most one of these four problems and none solved all four, because each is a bespoke one-off rather than an implementation of a known sync pattern (Singer/Airbyte's cursor+upsert model, or a CRDT/local-first merge). The fix isn't a better plugin per integration — several already exist, see below — it's recognizing this is one adapter problem solved six times.

## better-maintained alternatives found (2026-08-30 web search)

| Source note | Old tool / complaint | Better-maintained alternative found | Fixes which failure mode |
|---|---|---|---|
| [[2025-11-25 keepsidian issues]] | Keepsidian: no delete sync, manual dedupe-by-hand | Keepsidian itself, v1.1.2+ — added experimental two-way sync (opt-in, backup required) | #1, partially #4 |
| [[Glasp review]] | Glasp: all-or-nothing note download, no export back | Glasp Obsidian plugin v0.3.0 (July 2026) — incremental, non-destructive sync; matches existing notes **by source URL** and updates in place, no duplicates | #2, #3 (textbook upsert-by-stable-id) |
| [[Hypothesis review]] | weichenw/obsidian-hypothesis-plugin — one-directional, buggy | lindylearn/obsidian-annotations — forks it, adds true bidirectional sync (local edits push back to Hypothesis) | #1 |
| [[Github markdown to site]], [[review publish notes]], [[Obsidian web integration]] | mkdocs + hand-tuned CSS, whole day lost to theming | Quartz (+ Quartz Syncer plugin) — Obsidian-native wikilinks/backlinks/graph, GitHub Actions deploy, push-to-publish | not a sync-loop fix, but removes the CSS/build-maintenance burden driving the frustration |
| [[export goodreads to obsidian]] | Goodreads RSS 100-item cap, Goodsidian is a hand-run script | Booksidian (official community plugin, scheduled sync, choice to overwrite on update) and GoodReadSync (dedupes by a stored `bookID` frontmatter field) | #2 (GoodReadSync is upsert-by-stable-id done right) |
| [[obsidian-strava-sync]], [[strava sync backfill past data]] | obsidian-strava-sync: 30-activity page cap, create-only | strava-obsidian (saadsaifse) — explicit "smart sync" designed to catch backdated/edited uploads; Strava Periodic Note Sync — supports backfill up to 90 days | #2, #3 |
| [[Obsidian plugin - Tabber]] | no tabber existed, proposed one | Markdown Tabs and HTML Tabs — both now maintained community plugins | n/a (feature gap, not sync) |
| [[Obsidian private comments]] | proposed: comments stored outside the note, keyed by a hidden link | Side Comments — stores annotations as local JSON sidecar files, one per note, source markdown untouched | n/a (feature gap, not sync, but same "don't store the link in-band" idea already shipped) |

The single most useful finding: **Glasp's v0.3.0 plugin already implements the exact adapter pattern this proposal describes** — incremental fetch, match-by-stable-id (source URL), update-in-place, no duplicates. It's the existence proof that the pattern below is buildable, not speculative.

## proposed pattern: per-source cursor + upsert-by-stable-id

A future custom sync script (Strava, Keep, or anything new) should not reimplement sync per integration. One small generic core, one thin adapter per source:

**Adapter contract** (per source, ~3 functions):
- `fetch_since(watermark) -> records` — one page/batch of records newer than the watermark, plus the next watermark to persist
- `stable_id(record) -> str` — an ID stable across renames/edits (activity ID, book ID, source URL) — never the note's filename or title
- `to_markdown(record) -> frontmatter + body`

**Generic sync loop** (shared, written once):
1. Read `last_watermark` from a small state file (or frontmatter field) — not from "newest note in folder," which breaks on manual edits.
2. Call `fetch_since(last_watermark)`.
3. For each record, look up an existing note by `stable_id` (a frontmatter property, e.g. `strava_id`, not the filename — filenames can be renamed by the user).
4. Missing → create. Existing → diff and update in place, but only overwrite the plugin-owned section (below a marker like `<!-- synced -->`), leaving any human-added content above or after untouched.
5. Persist the new watermark **after every page**, not after the whole run, so an interrupted run resumes instead of restarting.
6. Keep "first full backfill" and "ongoing incremental sync" as two explicit entry points sharing steps 3–5, rather than one button that silently truncates when the history is long (this is exactly the fix proposed in [[strava sync backfill past data]]).
7. Deletions: don't propagate silently. Periodically diff the full remote ID list against local `stable_id`s and surface orphans for a human decision — matches [[2025-11-25 keepsidian issues]]'s actual ask ("ignore/delete notes, but don't silently lose the record").

This is the Airbyte/Singer "incremental + append-deduped" model (cursor field, at-least-once delivery, dedupe by primary key at the destination) applied to markdown notes instead of database rows, and it's the same idea Remotely Save's conflict handling and the Glasp plugin already use in narrower forms.

## sources
[[2025-11-25 keepsidian issues]] · [[Glasp review]] · [[Hypothesis review]] · [[Github markdown to site]] · [[export goodreads to obsidian]] · [[obsidian-strava-sync]] · [[strava sync backfill past data]] · [[Obsidian plugin - Tabber]] · [[Obsidian private comments]] · [[Obsidian web integration]] · [[review publish notes]]
