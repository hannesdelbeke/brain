---
created: 2026-08-30
tags:
- technical
- obsidian
- architecture
- proposal
aliases:
- cross-app entity registry proposal
- entity registry proposal
---

## The actual need

Nine notes in this vault independently hit the same wall: a note wants to link to something that lives in another app (a contact, a calendar event, a webpage, a WhatsApp call, a Unity asset, a URL shortcut) and there's no good place for backlinks to live, no single URI per thing, and no clean answer to "does the note wrap the external thing, or point straight at it." Each note re-derives a piece of the same missing layer instead of naming it.

That missing layer already has a design in this vault: [[2026-02 appagnostic Entity Registry - codex v2 plan]], refined from [[2026-02 app‑agnostic Entity Registry - copilot first pass]] and [[2026-02 app‑agnostic Entity Registry - codex feedback on copilot]]. This proposal doesn't design a new system — it points the 9 scattered notes at the existing one and recommends building it.

## The existing design, in brief

A local, app-agnostic **entity registry**: one canonical `entity` per real-world thing, with `entity_alias` (name variants), `entity_uri` (every openable link to it, prioritized, one marked primary), `external_record` (which source system knows about it, with provenance and change fingerprint), and `relationship` (typed links between entities — replaces ad-hoc backlinks). Source apps (Google Contacts, Obsidian, Strava, GitHub, calendar...) stay authoritative for their own data; the registry is only authoritative for cross-source identity, links, and "which URI do I open." Dedup is deliberately deferred — treat every source record as its own entity until duplicate noise actually hurts, then merge through a manual review queue, never auto-merge.

The v2 plan already answers the "build vs buy" question: build the thin registry (schema + `/search`, `/resolve`, `/entities/{id}`) yourself; don't build connectors or a matching engine from scratch — reuse existing sync/connector tooling and treat entity merging as manual-first. Its own next step is Phase 0 (schema + API skeleton) then Phase 1, a single vertical slice: Google Contacts → registry → an Obsidian command that searches and inserts links.

## How it resolves each open question

- [[choose if link to contacts opens linktree or app]] — the "linktree hub note OR direct app open, can't have both" framing is a false dichotomy once backlinks live in the registry's `relationship` table instead of on whichever note or app you open. `entity_uri` holds both the Obsidian note URI and the `Google contacts` URI for the same `entity_id`; `/resolve` picks one to open, but backlinks/mentions are visible regardless of which URI you followed.
- [[example of linking to a contact]] — "click the friend, see Instagram/WhatsApp/notes" is literally the `entity_uri` list (multiple URIs, one entity, prioritized). The "add a description, so I need a wrapper note in between" case for Strava is just another `external_record`/`entity_uri` row on the same `entity_id`, not a special middleman pattern.
- [[idea - auto link notes to calendar]] — calendar events become `entity` (kind=event); a note mentioning one is a `relationship` (mentions/participates_in). "Sorted by type in my review" is a `/search?kinds=event` query, no bespoke plugin needed.
- [[idea - open google calendar events from notes]] — autocomplete-on-tab into calendar events is exactly the Obsidian Phase-2 inline `[[` autocomplete provider already scoped in the v2 plan, with `entity_uri` (uri_type=web) pointing at the Google Calendar week/day view. Same connector pattern as Phase 1, just a second source.
- [[idea - insert notes in webpage]] — a webpage is an `entity` (kind=webpage, identified by URL); notes that annotate it are `relationship` rows. The "side window for detached notes" becomes a client of `/search`/`/resolve`, same shape as the browser-backlink-extension idea already floated in [[consider 2 sources of truth]].
- [[sync URL shortcuts to obsidian vault]] — this note's vault-file URL shortcuts are a hand-rolled, Obsidian-only stand-in for exactly `external_record` + `entity_uri`. The registry generalizes it and adds backlinks/search outside Obsidian too, which this note explicitly says the shortcut approach can't do.
- [[sync whatsapp calls to calendar]] — doesn't change the hacky notification/Tasker ingestion (still the hard part), but once ingested, the call becomes a `relationship` (participates_in) between a `contact` entity and an `event` entity, instead of a free-text name in the calendar event title.
- [[consider 2 sources of truth]] — this note independently re-derives the registry's own architectural stance ("a manager that auto-syncs two sources, the way Obsidian's backlink DB auto-syncs itself"). It's not a separate problem to solve; the v2 plan's registry *is* the manager this note is proposing, generalized past Obsidian.
- [[Game dev flow]] — mostly resolved the same way (asset ⇄ doc `relationship`, multi-URI per asset), with one gap: this note's git-branch/history link integrity (an asset merged in one branch, deleted in another) is **not** covered by the v2 plan, which has no notion of point-in-time/branch-scoped relationships. If pursued, that's a new phase (relationship rows scoped by commit/ref), not something Phase 0–3 already gives you.

## What web search adds beyond what's already in the Entity Registry notes

The existing notes already surveyed Solid, Memex, ActivityPub, Nango, Airbyte, Singer/Meltano, OpenRefine, and KDE Akonadi. Three more are directly relevant and weren't covered:

- **Tana's supertags** are the closest *working* analog to the `entity`/`relationship` model here: applying a supertag turns a node into a typed entity with fields, and a field that references another supertag creates an automatic bidirectional relation (tag a project's "Team lead" from `#person`, and the person automatically shows that project under a reference section) — validation that the typed-entity-with-auto-backlink shape is workable in a real shipping tool, not just a design doc.
- **Obsidian Personal CRM plugins** (`xuvi7/obsidian-personal-crm`, `TalkingQuickly/obsidian-crm`) already solve the narrowest version of [[choose if link to contacts opens linktree or app]] and [[example of linking to a contact]] today, inside Obsidian only, using nothing but wikilinks/backlinks/frontmatter and the metadata cache — no registry, no new infra. Worth checking before building anything: it may already scratch the itch for the contact case specifically, even though it doesn't generalize past Obsidian.
- **CardDAV/CalDAV** are the standard, already-solved sync protocols for exactly the contacts/calendar half of this problem (open standards, native iOS support, DAVx5/Radicale/Baikal on the rest). They're a candidate `external_record` source connector for Phase 1/Phase 3 contacts and calendar ingestion instead of hand-rolling the Google API pull the v2 plan currently assumes — same "outsource the connector" principle the plan already commits to, just naming a concrete non-Google option.

## Recommended next step

Don't design further. Implement the v2 plan's Phase 0 and Phase 1 as written: SQLite schema, `/search` + `/resolve`, a Google Contacts pull connector, and a minimal Obsidian command to insert links. That single slice directly resolves the two most-repeated notes ([[choose if link to contacts opens linktree or app]], [[example of linking to a contact]]) and establishes the connector pattern the calendar and webpage notes need next.

Before writing any code, spend fifteen minutes with `obsidian-personal-crm` — if it satisfies the contact-linking itch well enough, that's a smaller and faster win than standing up the registry, and the registry can still be built later for the sources (calendar, webpages, WhatsApp) the CRM plugin doesn't touch.

## Related notes
- [[2026-02 appagnostic Entity Registry - codex v2 plan]]
- [[2026-02 app‑agnostic Entity Registry - copilot first pass]]
- [[2026-02 app‑agnostic Entity Registry - codex feedback on copilot]]
- [[choose if link to contacts opens linktree or app]]
- [[example of linking to a contact]]
- [[idea - auto link notes to calendar]]
- [[idea - open google calendar events from notes]]
- [[idea - insert notes in webpage]]
- [[sync URL shortcuts to obsidian vault]]
- [[sync whatsapp calls to calendar]]
- [[consider 2 sources of truth]]
- [[Game dev flow]]
