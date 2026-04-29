---
views: 2
---
There’s a second limiter too:

  - after each import, obsidian-strava-sync-fork/src/StravaSync.ts updates settings.sync.lastActivityTimestamp
  - next time, it only asks for activities after that timestamp

  The settings UI even hints at this in obsidian-strava-sync-fork/src/SettingsTab.ts: it says imports are limited by the
  Strava API page limit and may need multiple runs.

  If you want, I can patch the fork so it paginates until it reaches all activities after the cutoff, instead of
  stopping at 30.


› how would a better UX be, without spamming strava servers etc. if i want all my data


• A better UX would separate two jobs clearly:

  1. Initial import
  2. Ongoing sync

  For “I want all my data”, I would not make the normal sync button pretend to do everything. I’d design it like this:

  Better UX

  - Import all history
      - One explicit action for first-time setup.
      - Shows a warning like: “This may take several minutes and multiple API requests.”
      - Paginates through all activities until exhausted.
      - Persists progress after each page so it can resume safely.
      - Shows progress like Imported 240 / ? activities or Page 8, 240 activities imported.
  - Sync recent changes
      - Fast everyday action.
      - Only fetches activities after the last successful sync timestamp.
      - Default button in the ribbon/command palette.
  - Resume import
      - If interrupted, continue from last page/cursor instead of restarting.
  - Import from Strava bulk export
      - Recommended path for users who truly want everything with minimal API load.
      - Best for backfill.
  - Rebuild / refresh selected range
      - Example: “re-sync last 90 days” or “re-sync activity by ID”.
      - Useful because edits to old activities otherwise get missed.

  Why this is better

  - Normal users get a fast sync.
  - Power users who want full history get an honest, durable workflow.
  - You avoid hammering Strava on every click.
  - You don’t hide API limits behind surprising behavior like “only last 30 activities”.

  Good defaults

  - First run:
      - Offer two buttons:
      - Quick sync recent activities
      - Import full history (slower)
  - If no local data exists:
      - Recommend bulk export first, API second.
  - If user chooses API full-history import:
      - Use pagination with conservative pacing.
      - Save after every page.

  How to avoid spamming Strava

  - Use paginated requests with a small delay between pages, for example 300ms to 1000ms.
  - Respect Strava rate limits and stop early if nearing them.
  - Cache detailed activity data locally.
  - Do not re-fetch unchanged older activities unless user explicitly requests a refresh window.
  - For normal sync, fetch summaries first, then fetch detailed records only for new or changed activities.
  - Persist sync state:
      - last_sync_started_at
      - last_sync_completed_at
      - last_history_page
      - last_activity_timestamp
  - Add a hard cap per run, like:
      - Import up to 300 activities this run
      - Then prompt to continue if needed.

  Best practical strategy if you want all data

  - Use Strava bulk export for the initial full backfill.
  - Then use API sync for new activities going forward.
  - Optionally add a periodic “refresh last 30/90 days” job for edits to titles/descriptions/notes.

  That hybrid model is the best balance of:

  - complete history
  - low API usage
  - predictable UX

  If you want, I can patch your fork to implement this as:

  - Import full history
  - paginated API fetch with resume state
  - Sync recent
  - optional bulk-export-first recommendation in settings.