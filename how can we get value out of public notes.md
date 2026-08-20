---
tags:
  - pkm
  - digital-garden
  - research
origin-sha: f202a3e0a
---
Extracting value from public [[Obsidian note|notes]] and [[digital garden|digital gardens]] (like [[public zettelkasten repos on high level concepts|public zettelkasten repos]]):

### High-signal Use Cases
- **bypass web slop:** use curated gardens as primary sources for human-tested configs, book notes, and systems thinking.
- **vault architecture inspiration:** adopt conventions like [[public/learnings from public zettelkasten vaults|principle-based naming]], maturity stages, and Maps of Content (MOCs).

### What Works vs Doesn't

High ROI

**curated seed notes**
keep a 1-page index of 5–10 authoritative links (see [[2026-08-20 domain masters hub]]). Zero upkeep, gives agents an instant high-trust starting point.

**on-demand agent fetching**
let agents query `llms.txt`, GitHub code search, or Jina Reader (`r.jina.ai`) on the fly. Zero local disk footprint or sync maintenance. See [[agent-friendly documentation tools]].

Low ROI

**local multi-vault embeddings**
cloning 10+ vaults to disk creates sync debt and dilutes search results with someone else's unfinished drafts. Only worth it for 1–2 massive, daily-use technical references.

**federated graphs & git submodules**
submodules create [[public/submodule wikilink clashes|wikilink collisions]] (e.g. conflicting `index.md` or `python.md`), detached HEADs, and ghost backlinks. Keep external notes as isolated reference docs, never linked into your primary graph.

### Credibility & Survival Filter
Most public vaults on [[GitHub]] are abandoned stubs or course-note dumps. Before trusting a public vault:
- **longevity:** verify multi-year commit history or active maintenance.
- **practitioner authorship:** ensure author is a working practitioner in that specific domain.
- **curated structure:** prefer finished reference wikis over raw, unedited streams of consciousness.

### References
