---
views: 1
---



strava has an API
consider using this to hook up to AI, to auto link URLs to posts.
strava has option to write both public and private notes per activity.
this can then be downloaded locally

## existing obsidian plugins

https://github.com/saadsaifse/strava-obsidian
- map preview in obsidian
- adds clutter `see strava activity details` to right click menu on notes in note file viewer in Obsidian
- [[YAML front matter]] so supports [[obsidian-dataview]]

https://github.com/watsonbox/obsidian-strava-sync
- more [[YAML front matter]] fields than the above one, also supports activity notes
- so far i prefer this one.

any others?
  - Custom sync service: build your own Strava app and push into the vault via script or Obsidian CLI. Best if you want
    exact filenames, custom linking rules, and note enrichment.
  - Custom webhook + polling hybrid: Strava officially supports webhooks for activity create/delete and some updates, b
    ut webhook update coverage is limited to title, type, and privacy. If you care about descriptions or private notes,
    webhooks alone are not enough; you still need periodic API fetches. Sources:
    https://developers.strava.com/docs/webhooks and https://developers.strava.com/docs/reference/
  - Automation platforms like Zapier/Make/n8n: workable if you want “new activity -> create note” without coding much,
    but usually worse than a custom script for structured Markdown and vault-safe updates.

  If your real goal is “auto-link Strava URLs inside existing notes,” I would not treat that as a plugin problem first.
  I’d use a custom sync job:

  - Pull activities from Strava API.
  - Store them in a local cache keyed by activity ID.
  - Use Obsidian CLI or direct file edits to insert/update links in matching notes.
  - Optionally use webhooks to trigger faster refreshes.

  That gives you much tighter control than the generic plugins.
## questions

- does it break if i rename a strava activity?
	- shouldn't if the note is named after activity ID
- do notes update / sync when strava activity is updated?

not with the current strava-sync plugin behavior; it creates new notes and skips existing ones
- so could be outdated info
- might lose connection if strava is tweaked or renamed.

## tech info why
 For the installed strava-sync plugin, the answer is mostly:

  - Renaming on Strava does not break identity if your filename includes the activity ID.
  - Existing notes do not automatically update when the activity is edited later.

  Why:

  The plugin creates files from the configured filename template, which defaults to {{id}} {{name}}, and it always
  includes id in the stored data. You can see that in C:/repos/pkm.obsidian/plugins/strava-sync/main.js. If you change
  the filename template to just {{id}}, a Strava title rename should not affect note identity at all.

  But the same code also shows the plugin only creates files and skips anything that already exists. Its serializer
  calls vault.create(...) and returns false on "File already exists" rather than updating the note. It also tracks
  lastActivityTimestamp and imports only later activities, not changed older ones. That means:
  
 If you want, I can patch the installed plugin so it updates existing activity notes by ID instead of skipping them.
