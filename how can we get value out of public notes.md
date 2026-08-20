---
tags:
  - pkm
  - digital-garden
  - research
---
Extracting value from public [[Obsidian note|notes]] and [[digital garden|digital gardens]] (like [[public zettelkasten repos on high level concepts|public zettelkasten repos]]) requires separating high-signal curation from low-ROI maintenance traps.

### high-signal use cases
Public gardens bypass web slop by providing human-tested configurations, book syntheses, and mental models without SEO fluff. They also serve as architectural inspiration for personal vaults, showcasing patterns like [[public/learnings from public zettelkasten vaults|principle-based note naming]], progressive maturity stages, and Maps of Content.

### what works vs what fails
The highest return on effort comes from lightweight, on-demand patterns. Maintaining a 1-page curated seed index of authoritative links (such as [[2026-08-20 domain masters hub]]) requires zero upkeep while giving [[AI agent|AI agents]] an instant high-trust starting point. When agents need specific docs, fetching them on-demand via `llms.txt`, GitHub code search, or Jina Reader (`r.jina.ai`) avoids local disk clutter and sync overhead. See [[agent-friendly documentation tools]].

Conversely, heavy infrastructure yields poor ROI. Cloning dozens of third-party vaults locally creates sync debt, requires constant maintenance, and dilutes semantic search results with someone else's unfinished drafts. Federated graphs and Git submodules cause [[public/submodule wikilink clashes|wikilink collisions]] across common filenames like `index.md` or `python.md`, alongside detached HEAD states and dead backlinks. External notes should remain isolated reference docs rather than nodes in your primary graph.

### credibility & survival filter
Most public vaults on [[GitHub]] are abandoned after a few weeks or consist of raw course copy-pastes. A public vault is worth consulting only if it has a multi-year commit history or active maintenance, is written by a working practitioner in that domain, and reads as a finished reference wiki rather than an unedited stream of consciousness.

### References
- [[2026-08-20 domain masters hub]] — curated seed list of authoritative domain vaults.
- [[agent-friendly documentation tools]] — tools for agents to ingest markdown without browsers.
- [[public/submodule wikilink clashes]] — why merging external vault graphs breaks wikilink resolution.