---
tags:
  - git
  - pkm
  - metadata
  - maintenance
aliases:
  - human vs AI authorship
---
## Summary
- **Cross-submodule migration problem:** Moving notes across submodule boundaries drops Git history, birth dates, and author attribution.
- **Privacy vs. provenance solution:** Use an anonymous `origin-sha: <sha>` pointer in frontmatter (0 repo name leaks) and record true human vs. AI authorship directly in the native Git commit author.
- **Workflow & audits:** 4-step detection plan applied to test cases ([[2025-12-02 laptop research]], [[2026-08-11 laptop research]]).

## Problem: Metadata Loss Across Submodules
Moving notes from [[private notes|private vault]] to [[public notes]] severs native Git history, dropping commit timestamps and author attribution. This metadata is essential to establish human vs AI text context and maintain [[wikilink temporal integrity|temporal integrity]].

## Restoring Earliest Creation Dates
To fix severed timestamps on migrated notes:
- **Earliest birth date recovery:** Sourced from original repo commit history or local filesystem creation date.
- **Migration log:** [[2026-08-18 Git history alignment and vault sync#4. PKM Git History Alignment (> 7 Days Gap)|Historical sync log]] for bulk date alignments.
- **Backdating plan:** [[retro add dates to old notes]] for ongoing chronological fixes.

## Cross-Submodule Migration Strategy
When publishing a note to `public/`:
- **Anonymous SHA pointer (default):** Store only `origin-sha: <sha>` in the public frontmatter. This leaks zero private repository or company names while letting local AI agents query your private vault for full line-by-line edit logs.
- **Selective patch migration (`git format-patch`):** For non-sensitive notes where public commit timestamps and author logs are desired.

See full trade-offs and Git commands in [[maintain git history between submodules]].

## Provenance and Git Author Detection Plan

When a note is moved from the private vault to `public/`, preserve the commit link and record true authorship in native **Git Author** rather than complex frontmatter:

**1. Detect origin commit SHA**
Query the private repository log for the last commit before migration:
```bash
git -C "C:/repos/pkm" log -n 1 --pretty=format:"%h" -- "note.md"
```

**2. Audit AI vs human text composition**
Inspect text patterns per [[algo to differentiate between AI and human notes]]:
- **LLM/Copilot markers:** Highly symmetric bold bullets (`- **Feature:** ...`), generic concluding formulas ("If you want X, pick Y"), emoji section headers, speculative future hardware claims.
- **Human markers:** Specific personal budget constraints, idiosyncratic phrasing, typo corrections, direct experience notes.

**3. Minimal frontmatter + native Git Author commit**
Keep the frontmatter minimal with only the origin SHA:

```yaml
---
origin-sha: 47c6734e6e0f
---
```

Record the actual text author directly in the Git commit author:
```bash
# Example: If written by Copilot/Claude, commit with AI author
git commit -m "add: note" --author="Microsoft Copilot <copilot@microsoft.com>"
# Example: If written by Human
git commit -m "add: note" --author="Hannes <...>"
```

## Test Case Audits
- **[[2025-12-02 laptop research]]:** Written 100% by [[Microsoft Copilot|Copilot]] (rigid symmetric feature bullets, speculative M5 chip, "shopping notes" formula). Origin SHA: `47c6734e6e0f`. Published with `origin-sha` and committed with Copilot Git author.
- **[[2026-08-11 laptop research]]:** Hybrid note (human specific pricing/used market constraints on ThinkPad X1 Yoga Gen 7/8 vs Razer Blade 15, structured by Gemini). Origin SHA: `645baa21b`.

### References
- [[maintain git history between submodules]] — Deep dive into submodule Git boundaries, recent commit examples, and migration trade-offs.
- [[human vs AI git history transfers between notes]] — How `git blame -C` detects extractions within a repo vs across submodules.
- [[linking to git commits and diffs in obsidian via uri]] — Linking directly to historical SHAs across repository boundaries.
- [[wikilink temporal integrity]] — Resolving historical links via preserved Git commit timestamps.
- [[2026-07-31 historic obsidian links]] — Mining Git history diffs to reconstruct graph evolution.


