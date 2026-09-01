---
tags:
- technical
- obsidian
- pkm
- planning
---

Which built-in Obsidian features are worth replacing with the local index in [[pkm metadata indexer]], now that the index and the daemon exist and a thin plugin already talks to them (see [[lightning-fast unified search plugin for obsidian]]).

## The rule that picks them

A core feature is worth reworking when it does one of two things:

1. It scans note content from top to bottom every time you ask. Backlinks, outgoing links and unlinked mentions do this, which is why they get slower as the vault grows. The index turns the scan into a lookup.
2. It only matches note titles. Quick switcher and the graph do this. Here the index does not just make it faster, it makes it able to answer questions it could never answer before, because it knows what notes mean and not only what they are called.

Features that only touch the note already open (outline, word count, page preview, bookmarks, daily notes) are already instant. The index buys them nothing, so leave them alone.

## Numbers from this vault

Measured from `.obsidian/pkm_index.db` on 2026-08-25:

- 3,228 notes, 6,550 sections, 6,550 embeddings, 9,256 wikilink edges.
- 2,185 notes have at least one inbound link, so 1,043 notes are orphans with nothing pointing at them.
- 1,780 edges are unresolved: wikilinks pointing at a note that does not exist.

## Action points

> [!todo] 1. Quick switcher that searches by meaning
> Right now, when you press the switcher and type, Obsidian only looks at the names of your notes. If you type "feeling overwhelmed by projects" and no note is called that, you get nothing, even though you wrote that note last year.
> The index already knows what every note is about, because every section has an embedding, which is a list of numbers describing its meaning. Notes about the same thing get similar numbers. So the switcher can find the note by its meaning instead of by its name.
> The work is small: [[search_vault.py]] already answers this exact query, and the plugin already opens a modal with mode prefixes. This is one more prefix, not a new window.
> Related: [[Obsidian - Tab Switcher]], [[random title note flow]], [[vault hybrid search]]

> [!todo] 2. Local graph that shows related notes, not only linked ones
> The graph only draws a line between two notes when you typed a link between them. 1,043 notes here have no line at all, so the graph cannot show them next to anything.
> Using the same meaning-numbers, the graph can draw a second kind of line: "these two notes are about the same thing, even though you never linked them". Orphans stop being lonely dots.
> Do the local graph, the one that shows the neighbourhood of the note you have open. The whole-vault graph stays an unreadable hairball at 3,228 notes either way, see [[vault graph complexity]].
> Related: [[Obsidian graph view]], [[2026-02 analyse my obsidian graph]], [[vault graph traversal]], [[orphan note]]

> [!todo] 3. Warn about duplicates when creating a note
> It is easy to write a third note about a thing you already wrote about twice, because you forgot the earlier ones existed.
> The check already exists: `index_pkm_meta.py --check-duplicate "some title"` lists notes that are already close in meaning. Agents working in this vault are told to run it. The "new note" command is not.
> Wire the check into note creation so the warning arrives before the duplicate is written, instead of surfacing months later.
> Related: [[agentic tooling upgrades over grep]], [[note linking duplicate source]], [[Evergreen notes]]

> [!todo] 4. Suggest tags for a new note
> Tagging by hand drifts, because you cannot remember which of your tags you used for this kind of note last time.
> Take the notes closest in meaning to the one being written, look at their tags, and offer the most common ones. The nearest neighbours are one query against the same embeddings.
> Related: [[2026-08-19 AI started tagging notes]], [[hashtag synonyms]], [[Obsidian note per tag]]

> [!todo] 5. Random note that surfaces orphans
> "Random note" picks any note with equal chance, so it usually lands on something well connected that you do not need to see.
> Pick at random from the 1,043 orphans instead. Every visit is then a chance to link a note that nothing points at, which turns a toy command into a habit that repairs the vault.
> Related: [[orphan note]], [[unlinked notes]], [[link unlinked notes]]

> [!todo] 6. Fix the 1,780 links that point nowhere
> Not a core feature, but the same query pays for it. 1,780 wikilinks point at notes that do not exist, either because a note was renamed or because the link was a typo.
> The `edges` table already stores every link with its source file and line number, so the list of broken links is one SQL query away, and each one can be shown with enough context to fix or delete it. This is the note [[note-link-janitor]], which is still on the unsolved list.
> Related: [[renaming notes breaks links]], [[wikilink temporal integrity]]

> [!todo] 7. Take the link half outside Obsidian
> Every feature above is the index serving one vault. The link database underneath it is not tied to Obsidian, or to markdown, or to one vault: anything that references anything can fill the same `edges` table, so the same queries answer "what points at this source file", "which docs does nothing reference", "which images are dead weight" across a repository or a whole organisation.
> The work is a scanner that derives edges instead of parsing `[[...]]`, plus a `corpus:path` node key so references can cross corpora. Designed in [[2026-08-27 a link graph over code, docs and assets]].
> Related: [[simple options for multi-repo agent search]], [[vault graph complexity]]

## Already done or in progress

- Core search is already replaced by the unified search modal over the daemon.
- Backlinks and outgoing links unlinked mentions: being served from the index, which also drops matches inside code blocks, the complaint in [[Obsidian unlinked mentions include code snippets]].

[[Obsidian core plugin]]
[[Obsidian improvements]]
[[vault hybrid search]]
[[finding unsolved problems in my vault]]
