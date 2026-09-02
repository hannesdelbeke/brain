---
date: 2026-09-01
created: 2026-09-01
tags:
  - pkm
  - architecture
---

> [!summary] eli5
> asked whether [[hierarchical map-reduce note rollup]] is worth building after reading [[why we did the agent hop tests]]. still not worth it, nothing changed since that note's own solved conclusion. the one new piece: the digest's token savings only count against a raw whole-vault dump (850k tokens), not against normal search, which already answers most queries near-free.
> **needs from you:** nothing, decision stands, this just records the reasoning for later.

> after reading "[[why we did the agent hop tests]]", is it still not worth it to build [[hierarchical map-reduce note rollup]]?
> ... (later) but 180k tokens is a lot of tokens, so it wouldn't do cost savings


### digest
On the digest — it's already fully spec'd, not built. From [[hierarchical map-reduce note rollup]] Plan section:
- a --digest flag on index_pkm_meta.py, prints one line per note straight from the existing DB — filename, tags, headings, summary_snippet
- zero API cost, no schema change, ~30 lines
- whole vault at that granularity is ~180k tokens, a tag-scoped slice like pkm is ~2k
- fallback only if the raw snippet proves too thin: add a paid --summarize pass (~$2.30 cold, cents per incremental run)

## still not worth the hierarchy

[[hierarchical map-reduce note rollup]]'s own conclusion, marked solved on 2026-08-25: not needed as designed, the vault fits one context as a flat digest (180k tokens), no time axis to recurse over, recursion only earns its keep at roughly 5x this vault's size or when one scope stops fitting the reducer's context. neither changed.

[[why we did the agent hop tests]] doesn't add a case for it either — its own conclusion calls the hop-chain approach a side track with no clear goal. what it actually asks for, read a summary first and only open the full note if needed, is the leaf-digest step from that plan, not the recursive rollup, and that step (a `--digest` flag on [[index_pkm_meta.py]]) still isn't built.

## the digest's savings need the right baseline

180k tokens sounds expensive until it's measured against the right alternative.

**search** already answers a normal "find a note" query near-free, a few hundred tokens through the semantic index, and never touches the digest at all.

**whole-vault synthesis** ("what themes ran through 2026", a cross-note audit) has no search query that answers it — the alternative there is dumping the raw markdown, about 850k tokens. the digest cuts that to 180k, roughly 4.7x, at zero api cost to build since it's fields already sitting in the index. that case is also rare, a few times a year per the rollup note, so even paying to run a model over the full 180k costs cents.

so the digest's win is only against the raw-dump path. skip it entirely if whole-vault synthesis never happens; it isn't a search replacement either way.

---

 the main things i m aiming for. if we e.g. only load headers in that might save many tokens comparedto loading whole note. and be enough to answer ai question

  Read 1 file, ran 1 shell command

There's already a dedicated concept note. Reading it.

  Read 1 file

Already exists — measured and mostly built: header extraction for token-efficient retrieval.md (2026-08-28, brain).

The idea itself: yes, headers-only beats loading the whole note. Measured on a real case (20-50 note scan): full body ~688 tokens/note vs extracted outline ~155 tokens/note, 77.5% reduction, 10-26k tokens saved per scan turn depending on candidate pool size. Enough to answer relevance questions ("is this the note I want") without reading the body.

Already built, not just theory: pkm-metadata-indexer already chunks at heading boundaries and stores path, heading, start_line, end_line per section in SQLite — that's what search_vault.py returns today (heading + line, not full text). The remaining gap the note flags: once a heading looks relevant, the agent should do an offset read (start_line–end_line only) rather than reading the whole file — that discipline isn't consistently followed, but the line boundaries needed for it already exist for free in the index.

Heading design matters — the note's case study found generic labels ("Overview") force a full read anyway (0% zero-read capability); assertion-style headers ("Label: core thesis") get to 100% zero-read while staying human-scannable.

So: no new note needed, no new build — the mechanism's there, the win is just using offset reads off the existing index instead of Read-ing the whole file.