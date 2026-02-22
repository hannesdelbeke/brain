---
views: 2
last viewed: 2026-02
---
Critique on [[2026-02 app‑agnostic Entity Registry - copilot first pass]]
next version [[2026-02 appagnostic Entity Registry - codex v2 plan]]
# critique

• Critique (ordered by impact)

High
- The note claims “single source of truth” while also saying you won’t modify source systems (line41, ...:15, ...:515). That makes the registry an index/cache, not true SoT. If you keep this contradiction, conflict handling will be messy.
- Entity merge/dedup is treated as a feature, but it is the core hard problem and is underspecified  (...:122, ...:127, ...:377). You need explicit identity strategy per type (hard IDs first, probabilistic match second, manual review queue).
- “No existing solution does this” is overstated (...:541, ...:700, ...:741). No single perfect product, yes. But many mature parts already exist; building all layers yourself is high maintenance.

Medium
- URI model is optimistic about app URI support (...:74 to ...:78). For many apps, web URL is stable but app URI is not guaranteed/cross-platform.
- Sync model is too thin for production reality (...:117 to ...:123): missing tombstones/deletes, rate limits, retries, cursor invalidation, idempotency, and replay.
- Security/privacy is barely addressed despite centralizing sensitive personal metadata. Need threat model + encryption-at-rest + per-plugin scopes.

Low
- The doc has mojibake/encoding artifacts and heavy repetition, which hides the good core idea (...:4, ...:7, many sections duplicated).

---

  - Connector + sync layer: Nango (custom unified APIs, syncs, checkpoints, delete detection).
    https://nango.dev/docs/implementation-guides/use-cases/unified-apis
    https://nango.dev/docs/implementation-guides/use-cases/syncs/implement-a-sync
  - Bulk connectors/replication: Airbyte (600+ connectors).
    https://docs.airbyte.com/
  - OSS connector standard/ecosystem: Singer/Meltano (tap/target model).
    https://hub.meltano.com/singer/spec/
  - Entity matching workflow: OpenRefine reconciliation/record linkage.
    https://openrefine.org/docs/manual/reconciling
  - Obsidian deep linking (don’t invent URI format):
    https://help.obsidian.md/uri
  - Closest “local multi-source PIM registry” precedent: KDE Akonadi (for PIM domain).
    https://develop.kde.org/docs/features/akonadi/
  - Philosophical/data-ownership adjacent model: Solid Pods.
    https://solidproject.org/faqs

  **Pragmatic recommendation**
  Build only the thin “entity registry + resolver API” yourself; outsource connectors/sync and matching first. That gives you app-agnostic value without owning an integration platform from day 1.
  
---
explain more

Thin entity registry = the local SQLite schema + APIs (/search, /resolve, entity → URIs, relationships, review queue)  that do identity resolution once data is already available. You build that yourself because it’s the novel thing you
care about.

Outsource connectors/sync: defer writing full connector suite; instead reuse something like **Airbyte/Nango/Singer** to pull data or mirror only the sources you currently need. Those tools already handle OAuth, rate limits, pagination,
retries, change detection, and schema drift.

Matching first: ~~don’t write a complex dedupe engine up front. Collect the raw records from your connectors and make dedup/match decisions manually or with simple heuristics before automating merges.~~
%%yeah i don't care about dedupe%%

This lets you deliver app-agnostic linking (the registry + resolver) without spending months building a full integration platform.

---

 what is dedupe for. i m not sure if i care for it

• Deduplication purpose

- It keeps each conceptual entity (person, note, activity, etc.) represented once in the registry so autocomplete/linking doesn’t show duplicate hits for the same real-world thing. Without it you get `Alice (Google Contacts)`, `Alice (Obsidian note)`, `Alice (GitHub)` all listed and the registry loses that unified identity benefit.
- It’s not just cosmetic: downstream features like [[backlink|backlinks]], relationship graphs, preferred URI resolution, and write-back all depend on a single canonical entity so you can merge metadata, choose the right URI to open, and keep relationships consistent.
- You can skip heavy automation early. **Start by treating every source record as its own entity**, then add a “merge when confident” review queue. Only automate simple cases (e.g., identical Google ID) later. Focus on the things you care about; **dedupe can be added later** incrementally when the duplicate noise starts to hinder workflows.