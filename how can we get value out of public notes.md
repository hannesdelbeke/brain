---
tags:
  - pkm
  - digital-garden
  - research
---
Strategies to extract value from public [[Obsidian note|notes]] and [[digital garden|digital gardens]], like
- [[public zettelkasten repos on high level concepts|high level public zettelkasten repos]]
- [[digital garden examples]]

### high-signal research
- bypass SEO clickbait and AI-generated fluff with human-tested workflows, book notes, and configs.
- treat curated gardens as primary sources before browsing broad web results.

### local semantic retrieval
- clone high-signal vaults locally and index with [[public/offline GPU embeddings with incremental cache|offline GPU embeddings]].
- search third-party notes from CLI or [[AI agent|AI agents]] without polluting your personal graph.

### vault architecture inspiration
- adopt naming conventions like [[public/learnings from public zettelkasten vaults|principle-based note titles]] and maturity stages.
- borrow working Maps of Content (MOCs) and visual canvas layouts.

### federated graphs
- link across peer vaults with Git submodules or URI schemes.
- adopt the Agora model to build distributed knowledge webs across creators.
- [[interwikilinks plugin]] discusses similar interwiki link concepts

### discovery: how to find the right vault
- **manual lookup doesn't scale:** you won't remember which niche vault holds a specific fix.
- **automated agent GitHub search:** agents query GitHub code search directly filtered by markdown paths (`path:notes/`, `path:content/`, `extension:md`) when solving questions.
- **local multi-vault embedding index:** clone top gardens into a local `references/` folder and embed them with [[public/offline GPU embeddings with incremental cache|offline GPU embeddings]]. The agent queries your vault and third-party references simultaneously in milliseconds.
- **curated specialist seeds:** maintain a small list of domain masters (e.g. graphics tech art, nix, knowledge architecture) as default search targets for agents before falling back to noisy web searches.
example: [[2026-08-20 domain masters hub]]