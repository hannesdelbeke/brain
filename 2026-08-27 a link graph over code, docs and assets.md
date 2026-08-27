---
date: 2026-08-27
created: 2026-08-27
tags:
  - technical
  - pkm
  - search
  - graph
  - planning
aliases:
  - 2026-08-27 a link graph over code, docs and assets
  - link graph beyond the vault
  - graph over repos and docs
---

# A Link Graph over Code, Docs and Assets

[[core Obsidian features to rework on the vault index]] asks which built-in features the local index can replace inside one vault. This note asks the next question: the index is a search engine and a link database, and only one of those two is tied to Obsidian at all. The link half works on anything that references anything.

The vault has wikilinks, so its `edges` table is filled by parsing `[[...]]`. A repository has no wikilinks and is full of references anyway: a readme pointing at a source file, an import naming a module, a markdown page embedding a diagram, a service doc naming another service. Those are edges nobody stores, so nobody can query them.

## What already generalises

Three things carry over unchanged.

The schema. `notes`, `sections` and `edges` describe documents, chunks and references. Nothing in those three tables says "markdown" or "vault".

The scanner contract. Any callable returning `(notes, sections, links, errors)` indexes into the same tables, which is how a transcript corpus and a repository catalog already sit beside a vault in one daemon. A repository scanner is another one of those, not a second system.

The retrieval. Embeddings and BM25 over sections work the same on a source file's docstring as on a note's paragraph.

## What does not, and is the actual work

Edges have to be derived rather than parsed, because outside a vault an author never wrote a link at all. The candidates, cheapest first:

- markdown links and image embeds, which are already explicit and only need resolving to a path
- relative path references in prose, `see src/auth/token.py`, which are a regex and a file-exists check
- imports and includes, one small parser per language, and the point at which this stops being cheap
- an artifact named in text without a link, which is the unlinked-mention problem the vault index already solves, applied across corpora rather than within one

The other missing piece is a global identity for a node. Inside a vault a path is unique; across repos it is not, so a node key is `corpus:path` and cross-corpus edges resolve against that. That is the one schema change the whole idea needs, and it is small.

## What it answers that nothing does today

Which documents describe this file. Answered today by asking whoever wrote it.

Which documents nothing references, which is the orphan query from the vault applied to docs. A doc no code and no other doc points at is either the entry point or dead, and the graph plus a glance tells you which.

Which assets nothing references. Images and diagrams accumulate in repos exactly the way orphan notes accumulate in a vault, and neither has a delete-safely check today.

Which repositories reference each other, when the reference is a url in a readme rather than a package dependency. Dependency graphs see the manifest and miss the prose, and the prose is where the "we call their api" relationships live.

## Why it is not the graph view again

[[vault graph complexity]] is the warning: a whole-vault graph at 3,228 notes is an unreadable hairball, and a graph over an organisation's repositories would be worse by orders of magnitude. So this is a query surface, not a picture. The useful outputs are lists — what points here, what this points at, what points at nothing — and the local neighbourhood of one artifact, which is the same conclusion the vault reached.

## v0

One scanner over one repository, emitting edges for markdown links, relative path references and image embeds only. No imports, no cross-repo resolution, no new UI.

Acceptance is two queries answered from the index: every document that references a given source file, and every image in the repository that nothing references. Both are one SQL query against `edges` once the rows exist, and both are impossible today without reading the repository by hand.

If those two answers are useful on one repository they are useful on fifty, and the import parsers and cross-corpus resolution earn their keep at that point rather than before it.

## Related

- [[core Obsidian features to rework on the vault index]] — the same index, applied inside one vault
- [[pkm metadata indexer]] — the scanner contract and the three tables
- [[simple options for multi-repo agent search]] — the earlier pass at searching across repositories
- [[vault graph complexity]] — why the answer is a query, not a picture
- [[unlinked mentions from the vault index]] — the mention-without-a-link problem this generalises
- [[note-link-janitor]] — broken links as a query, the same idea one corpus down
