---
tags:
  - git
  - pkm
  - metadata
  - maintenance
aliases:
  - human vs AI authorship
---
To establish and preserve the context of whether a human or AI wrote a piece of text (and when), several interconnected strategies are used across the vault:

- **Authorship Detection & Attribution:** 
  We use native Git commit authors (e.g. `--author="Antigravity <ai@antigravity>"`) instead of YAML tags to track who wrote what. 
  See [[algo to differentiate between AI and human notes]] for heuristics and test case audits on detecting legacy AI text.

- **Cross-Submodule Migrations:** 
  Moving notes drops metadata. 
  To preserve authorship context and history safely without leaking private vault data, use an `origin-sha` pointer or synthetic commits. See [[maintain git history between submodules]].

- **Temporal Integrity:** 
  Because Git resets creation timestamps on moved files, we pull the original birth date via Git log and inject it as `created: YYYY-MM-DD` in frontmatter. See [[moving files across submodules loses created date]].

### References
- [[human vs AI git history transfers between notes]] — How `git blame -C` detects extractions within a repo vs across submodules.
- [[linking to git commits and diffs in obsidian via uri]] — Linking directly to historical SHAs across repository boundaries.
- [[2026-07-31 historic obsidian links]] — Mining [[git history|Git history]] diffs to reconstruct graph evolution.
