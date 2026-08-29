---
date: 2026-08-29
created: 2026-08-29
tags:
  - pkm
  - search
  - ai
  - graph-theory
  - architecture
---

# 🕸️ Stub vs Hub: When a Link-Only Note Has Value

Word count alone can't tell a dead stub from a real hub note. A 5-word note can be a load-bearing claim; a 200-word note can be padding around zero information. Check prose-to-link ratio, edit history, and backlink direction instead.

Related: [[vector search obsoletes empty stub wikilinks]], [[2026-08-27 synapse links vs wikilinks and semantic links|synapse links vs wikilinks]], [[when to request wikilinks from AI]]

---

## Signals a note is a dead stub (safe to remove/inline)

- Near-empty: frontmatter plus one bracket, no prose sentence explaining why the note exists.
- Zero backlinks except the one link that spawned it; created once, never edited again (single commit in git log).
- Title is a bare entity name (`Gemini Flash 3.7`), not framed as a concept or claim.
- Vector search on its title surfaces the same content already covered in another note — redundant, not missing.

## Signals a note is a real MOC/hub (keep, even if link-only)

- Title reads as aggregation intent: "overview", "index", "notes on X", a dated session note.
- Links sit inside explanatory prose ("see [[X]] for Y, because Z"), not a bare list.
- Multiple edits over time in git log, not one-shot creation.
- Backlinks pointing *into* it from several other notes — the vault already treats it as a hub.

## Cleanup pass plan

1. Grep every `[[...]]` target across the vault; sort into missing file (dead stub), near-empty file (dead stub candidate), and real note.
2. For each stub candidate, check git log (one commit = suspect) and backlink count.
3. Run the vault's own semantic search ([[public/skills/pkm-metadata-indexer/SKILL|pkm metadata indexer]]) on the stub's title. If a real note already covers it, mark for deletion and redirect inbound links to the real note, or unbracket to plain text per [[vector search obsoletes empty stub wikilinks]]'s rule of thumb.
4. Anything ambiguous — prose exists, backlinks exist, but thin — gets flagged for human review, not auto-deleted.

## Model choice for running the pass

Most of the classification is mechanical (word count, link count, git log, index lookup), not deep reasoning — that work is cheap and parallelizes across many notes. Fan it out across many Sonnet 5 subagents rather than one sequential pass. Reserve a stronger model (Opus) only for the notes that land in the ambiguous bucket in step 4, where judging "does this prose carry real meaning" actually needs it.
