---
tags:
  - pkm
  - digital-garden
  - research
---
Strategies and practicality reality check for extracting value from public [[Obsidian note|notes]] and [[digital garden|digital gardens]] (like [[public zettelkasten repos on high level concepts|public zettelkasten repos]]):

### high-signal use cases
- **bypass web slop:** use curated gardens as primary sources for human-tested configs, book notes, and systems thinking.
- **vault architecture inspiration:** adopt conventions like [[public/learnings from public zettelkasten vaults|principle-based naming]], maturity stages, and Maps of Content (MOCs).

### practicality reality check: what works vs what fails
- **curated seed notes (high ROI):** keep a 1-page index of 5–10 authoritative links (see [[2026-08-20 domain masters hub]]). Zero upkeep, gives agents an instant high-trust starting point.
- **on-demand agent fetching (high ROI):** let agents query `llms.txt`, GitHub code search, or Jina Reader (`r.jina.ai`) on the fly. Zero local disk footprint or sync maintenance.
- **local multi-vault embeddings (low ROI):** cloning 10+ vaults to disk creates sync debt and dilutes search results with someone else's unfinished drafts. Only worth it for 1–2 massive, daily-use technical references.
- **federated graphs & git submodules (avoid):** submodules create [[public/submodule wikilink clashes|wikilink collisions]] (e.g. conflicting `index.md` or `python.md`), detached HEADs, and ghost backlinks. Keep external notes as isolated reference docs, never linked into your primary graph.

### credibility & survival filter
Most public vaults on GitHub are abandoned stubs or course-note dumps. Before trusting a public vault:
- verify multi-year commit history or active maintenance.
- ensure author is a working practitioner in that specific domain.
- prefer finished reference wikis over raw, unedited streams of consciousness.

### related notes
- [[2026-08-20 domain masters hub]] — curated seed list of authoritative domain vaults.
- [[agent-friendly documentation tools]] — tools for agents to ingest markdown without browsers.
- [[public/submodule wikilink clashes]] — why merging external vault graphs breaks wikilink resolution.