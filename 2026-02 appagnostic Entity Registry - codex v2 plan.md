# App-Agnostic Entity Registry (Codex v2 Plan)

## Purpose
Build a local, app-agnostic entity registry that powers linking/autocomplete across tools (starting with Obsidian) without becoming a full sync platform.

## One-sentence definition
A local identity and link-resolution layer that maps one logical entity to many source records and openable URIs.

## Scope (v2)
- Local-first SQLite registry.
- Entity identity + aliases + canonical labels.
- URI resolver (web/app/local URI per entity).
- Search API for autocomplete and link insertion.
- Read-only ingest from selected sources first.
- Explicit provenance for every field.

## Non-goals (for v2)
- Full bidirectional sync for every source.
- Automatic perfect deduplication.
- Replacing source systems as source of truth.
- Building a full graph database product.

## Architectural stance
- Source systems remain authoritative for their native objects.
- Registry is the authoritative layer for:
  - cross-source identity mapping
  - cross-source links/relationships
  - preferred open URI resolution

## Data model (minimal, practical)

### `entity`
- `id` (UUID)
- `kind` (person, note, repo, activity, photo, etc.)
- `canonical_label`
- `status` (active, merged, archived)
- `created_at`, `updated_at`


• Entity aliases let each canonical entity carry all the variations that sources and eyeballs use, so your registry
  keeps one clean identity while still matching fuzzy queries and different contexts.

- When a Google contact is “Hannes Müller” and Obsidian note is “H. Muller,” an alias entry ties both strings to the same entity without altering either source.
- Aliases support rapid lookup (search for nicknames, abbreviated names, legacy handles) and let the resolver present the right label depending on where the request came from (e.g., use “Alice from GitHub” vs “Alice Johnson contact”).
- They also keep a record of provenance—each alias carries a source tag, so when you inspect an entity you see every variant the system has seen and can decide whether to merge, prefer one URI, or flag outdated labels.
### `entity_alias`
- `id`
- `entity_id`
- `alias`
- `source`

### `external_record`
- `id`
- `source` (google_contacts, github, strava, obsidian, etc.)
- `source_record_id`
- `entity_id`
- `fingerprint` (hash for change detection)
- `raw_ref` (pointer/metadata, not full payload)
- `first_seen_at`, `last_seen_at`, `deleted_at`

### `entity_uri`
- `id`
- `entity_id`
- `uri`
- `uri_type` (app, web, local)
- `source`
- `priority`
- `is_primary`

### `relationship`
- `id`
- `from_entity_id`
- `to_entity_id`
- `rel_type` (mentions, appears_in, owns, participates_in)
- `source`
- `confidence` (0-1)

### `sync_state`
- `source`
- `cursor`
- `last_success_at`
- `last_error`

## skip
### `review_queue`
- `id`
- `candidate_a_entity_id`
- `candidate_b_entity_id`
- `reason`
- `score`
- `state` (pending, accepted, rejected)

## Identity and dedup strategy
Deterministic first, probabilistic second.

1. Hard identity keys (best): source immutable IDs, verified email, verified phone, stable username.
2. Strong composite keys: normalized name + domain + additional source-specific anchors.
3. Fuzzy suggestions only: push uncertain matches to `review_queue`.
4. Never auto-merge low-confidence matches.

## API (local)
- `GET /search?q=...&kinds=...`
- `GET /entities/{id}`
- `GET /entities/{id}/uris`
- `POST /resolve` (input: entity_id, preferred_context)
- `POST /sync/{source}`
- `POST /review/{id}/accept|reject`

## Build vs buy decisions
Use existing tools where they reduce maintenance burden.

- Connectors/sync transport:
  - Start with direct source SDK/API for 1-2 sources.
  - Evaluate Nango/Airbyte/Singer if connector count grows.
- Reconciliation workflow:
  - Reuse OpenRefine-style review concepts for merge decisions.
- Storage/search:
  - SQLite + FTS5 first; postpone heavier graph DB.

## Security and reliability baseline
- OAuth tokens encrypted at rest.
- Per-source least-privilege scopes.
- Append-only sync logs for audit/debug.
- Idempotent sync jobs (safe retries).
- Tombstone handling for deletes.
- Daily DB backup + weekly restore test.

## Obsidian integration strategy
Phase 1: command palette + modal search.
Phase 2: inline `[[` autocomplete provider.
Phase 3: enrich link insertion with URI choice (note/web/app).

## Practical next steps

### Phase 0 (1-2 days): Foundations
- Finalize schema and migration setup.
- Stand up local API skeleton.
- Add seed data + test fixtures.
- Define normalization helpers (names, emails, URIs).

### Phase 1 (3-5 days): First vertical slice (Google Contacts -> Obsidian)
- Implement `google_contacts` pull-only connector.
- Map records to `external_record` + `entity` + `entity_uri`.
- Implement `/search` and `/resolve`.
- Build minimal Obsidian command to query and insert links.
- Add manual merge review endpoint.

### Phase 2 (3-5 days): Hardening
- Incremental sync with cursor and retries.
- Tombstone/deletion support.
- FTS ranking improvements.
- Add backup/restore scripts.
- Add observability (sync metrics + structured logs).

### Phase 3 (1 week): Second source + merge quality
- Add GitHub OR Strava connector (pick one).
- Implement cross-source candidate matching.
- Expand review queue UX.
- Add regression tests for merge safety.

## Milestones and exit criteria
- M1: Can search and insert links from Google Contacts in Obsidian.
- M2: Sync is repeatable and idempotent; no duplicate explosion.
- M3: Manual review queue controls all uncertain merges.
- M4: Two sources coexist under one entity model without schema churn.

## Explicit risks
- Dedup errors can silently corrupt trust.
- Connector maintenance can dominate project time.
- Obsidian autocomplete integration may have UX/perf constraints.

## Risk controls
- Manual-review-first merge policy.
- Keep connectors shallow and read-only early.
- Ship one end-to-end slice before adding sources.

## Decision log (current)
- Local-first: yes.
- App-agnostic: yes.
- Source-of-truth claim: corrected (sources for native objects, registry for identity/linking).
- Write-back: deferred until read path is stable.

## Immediate TODO checklist
- [ ] Create SQLite schema + migrations.
- [ ] Implement `/search` + `/resolve`.
- [ ] Implement Google Contacts pull connector.
- [ ] Build tiny Obsidian integration (command first).
- [ ] Add review queue UI/API.
- [ ] Add backup + restore verification script.
