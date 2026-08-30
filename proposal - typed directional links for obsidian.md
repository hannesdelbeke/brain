---
date: 2026-08-30
created: 2026-08-30
tags:
  - technical
  - planning
  - obsidian
  - pkm
aliases:
  - typed directional links proposal
  - unified link model proposal
---
22 notes in this vault each hit a wall with `[[wikilink]]`, and each one treated its wall as a one-off. They aren't one-off. They're the same missing primitive, approached from 22 angles.

## The missing primitive

A `[[wikilink]]` hardcodes one specific combination of four independent properties every link actually has:

| Property | What `[[wikilink]]` assumes | What notes below actually need |
| :--- | :--- | :--- |
| **direction** | bidirectional (always shows in both notes' backlinks) | sometimes one-directional (a hub note shouldn't backlink to every leaf) |
| **type** | untyped (a link is a link) | semantic (`parent`, `blocks`, `example-of`, `disagrees-with`...) with optional strength/weight |
| **target-kind** | internal note, same vault, current file only | external URL, another vault/submodule, a hashtag, a git commit of a note |
| **temporal validity** | resolves to `HEAD` always | sometimes should resolve to "what the target looked like when I linked it" |

Obsidian ships exactly one point in that 4-dimensional space. Every note below is someone reaching for a different point and finding no primitive there, then improvising a workaround (frontmatter fields, HTML anchors, external scripts, a second vault, a request on the Obsidian forum).

## Each note's specific wall

| Note | Wall |
| :--- | :--- |
| [[1 directional annotations]] | private annotations need to attach to a source (Slack thread, Google Doc) that can't hold a backlink at all |
| [[2026-02-16 an example of bad cross app linking]] | a URL has no backlink support, so a note can't be found by searching the URL it references |
| [[2026-07-31 historic obsidian links]] | links removed during a refactor vanish from the graph; the history still exists in git but Obsidian never surfaces it |
| [[Obsidian - one way wikilinks]] | wants a non-reciprocal `[[>note]]` so hub notes (Obsidian, Windows) don't drown in backlink noise; also wants type + strength |
| [[Obsidian find dead links]] | wants to find every dead/broken link across a folder, not just per-note |
| [[Obsidian redirect for notes]] | wants a redirect primitive: point at a URL/note once, update every reference when the source moves |
| [[TODO include project wikis in Obsidian]] | importing an external wiki collides note names with the existing vault, silently rewriting wikilinks on both sides |
| [[URI link to obsidian git diff - RnD]] | wants a link that resolves to one specific git commit/diff of a note, not always `HEAD` |
| [[interwikilinks plugin]] | wants `[[sitename:page]]`-style interwiki links to external wikis/sites — doesn't exist |
| [[link type]] | wants to say *why* two notes relate (`parent`, `blocking`, `duplicate`, JIRA-style), not just that they do |
| [[link unlinked notes]] | orphan notes are undiscoverable, because nothing forces a link into existence |
| [[link unlinked websites]] | wants inline reference/annotation links directly on arbitrary external websites, not just vault notes |
| [[make wikilinks optional]] | wants implicit linking of unlinked mentions without littering source text with `[[ ]]` |
| [[hashtag synonyms]] | wants synonymous hashtags (`#plugin` `#addon` `#extension`) merged or aliased |
| [[github wikis in obsidian & interwikilinks]] | interwiki links work in neither Obsidian nor GitHub, blocking cross-vault wiki linking on both ends |
| [[renaming notes breaks links]] | renaming a note breaks external URLs (a published site, another site's link to it) pointing at the old name |
| [[submodule wikilink clashes]] | two git submodule vaults sharing a note name collide when loaded into one vault, and any fix desyncs the submodule |
| [[wikilink temporal integrity]] | a link should resolve to what the target looked like when the link was written, not always `HEAD` |
| [[note linking duplicate source]] | no way to link an external URL/repo directly with tags and metadata, only via a duplicate proxy note |
| [[note-link-janitor]] | (this note documents an existing tool rather than a gap — see below) |
| [[age links]] | wants link strength to change dynamically with usage (click frequency, recency) instead of staying static |
| [[Link strength]] | wants to distinguish close vs. loose relations (a weighted/qualified edge) instead of one flat link |

## What already exists

Web search confirms two of the 22 notes already name a real, existing tool rather than a gap:

- **note-link-janitor** is real: [andymatuschak/note-link-janitor](https://github.com/andymatuschak/note-link-janitor), a Node script that injects a computed backlinks section into each Markdown file, used for static-site backlinks (the vault's fork is [hannesdelbeke/note-link-janitor](https://github.com/hannesdelbeke/note-link-janitor)). Matuschak's own README states he intended to extend it to detect broken links and orphans, but never did — so the janitor never became the dead-link/orphan tool [[Obsidian find dead links]] and [[link unlinked notes]] want.
- **interwikilinks plugin** is *not* an existing tool — the note is the author's own design sketch. Search confirms no maintained Obsidian plugin does true cross-vault interwiki resolution (`[[sitename:page]]`). The closest things are the manual `obsidian://vault/<vault>/<note>` URI (already known to the author) and Logseq's `logseq://graph/<graph>?page=<page>` scheme, which has the same UX gap: it works, but isn't a first-class wikilink.

Beyond those two, other plugins/tools cover pieces of the wider problem:

- **Breadcrumbs** ([SkepticMystic/michaelpporter](https://github.com/michaelpporter/breadcrumbs)) — typed, directional links (`parent`/`child`, `next`/`prev`, custom types) built from frontmatter, tags, or naming schemes, rendered as a separate directed graph from Obsidian's native one. Solves [[link type]] and half of [[Obsidian - one way wikilinks]] (direction) for internal notes. Gap: no external-URL or cross-vault target support, no temporal resolution.
- **Broken Links** and **Find orphaned files and broken links** (community plugins), plus the browser-based [recal broken-link checker](https://www.recal.so/tools/markdown-broken-link-checker) — directly solve [[Obsidian find dead links]] and the orphan-detection half of [[link unlinked notes]]. `recal` even suggests the renamed target when a rename broke a link.
- **Tag Wrangler** ([pjeby/tag-wrangler](https://github.com/pjeby/tag-wrangler)) — renames/merges tags vault-wide and supports tag-page aliases. Directly solves [[hashtag synonyms]].
- Obsidian's own **Settings → Files & Links → Automatically update internal links** (on by default) already rewrites in-vault wikilinks on rename. It does not touch external URLs pointing at a published note, which is the actual complaint in [[renaming notes breaks links]] — that half stays unsolved.
- **obsidian-weighted-graph** ([jamesms36](https://github.com/jamesms36/obsidian-weighted-graph), `[[Note]]::weight` syntax) and **Graph Link Types** (labels edges from Dataview fields) — a static numeric or typed weight on an edge, i.e. [[Link strength]]. Neither one ages a weight over time or usage, so [[age links]] stays unsolved.
- **Tana** is the one mainstream PKM tool with typed, directional relations built into its core model (supertags with directional fields), unlike Roam/Logseq, which — like Obsidian — keep links bidirectional and untyped. Confirms this is a real, general PKM gap, not an Obsidian-specific oversight.
- No tool found (Obsidian or otherwise) resolves a link to the target's state *at link-creation time* rather than `HEAD` — [[wikilink temporal integrity]], [[URI link to obsidian git diff - RnD]], and [[2026-07-31 historic obsidian links]] all remain open; [[Obsidian plugin - Git]] provides the raw git history these would need to build on, but nothing wires it into link resolution today.
- No plugin resolves the submodule/multi-vault name-clash case ([[submodule wikilink clashes]], [[TODO include project wikis in Obsidian]]) without desyncing the submodule.

## Recommendation

Don't build one plugin for all four dimensions — the notes above span at least four genuinely separate problems with different existing coverage. Instead:

1. **Adopt Breadcrumbs** for link type + direction on internal notes. It already covers [[link type]] and [[Obsidian - one way wikilinks]] and is actively maintained.
2. **Adopt Tag Wrangler** for [[hashtag synonyms]] — already solved, just install it.
3. **Adopt Broken Links / Find orphaned files and broken links** for [[Obsidian find dead links]] and [[link unlinked notes]] — already solved.
4. **Confirm "Automatically update internal links" is on** (it is by default) — closes the in-vault half of [[renaming notes breaks links]]; the external-URL half has no fix and isn't worth building one for.
5. **For what's left unsolved** — external-URL/target-kind links, temporal resolution, cross-vault/submodule name clashes — don't build a plugin. Add a minimal frontmatter convention instead:
   ```yaml
   links:
     - target: "https://forum.obsidian.md/t/..."
       type: reference
       direction: out
       kind: external
     - target: "[[Note B]]"
       type: example-of
       direction: out
       kind: internal
       valid_at: 2026-02-16
   ```
   Query it with Dataview. This degrades to plain YAML everywhere the vault already has to survive (git diffs, GitHub rendering, other Markdown tools, [[note-link-janitor]]'s own parser), which is the same reason the vault already keeps `[[wikilink]]` in the body for native navigation rather than replacing it. Build only the Dataview query, not a plugin — the four notes about custom link syntax ([[Obsidian - one way wikilinks]], [[Obsidian redirect for notes]], [[interwikilinks plugin]]) all independently conclude the same thing: a real plugin is a lot of edge-case work for a small UX gain.

## Related Notes

[[1 directional annotations]] · [[2026-02-16 an example of bad cross app linking]] · [[2026-07-31 historic obsidian links]] · [[Obsidian - one way wikilinks]] · [[Obsidian find dead links]] · [[Obsidian redirect for notes]] · [[TODO include project wikis in Obsidian]] · [[URI link to obsidian git diff - RnD]] · [[interwikilinks plugin]] · [[link type]] · [[link unlinked notes]] · [[link unlinked websites]] · [[make wikilinks optional]] · [[hashtag synonyms]] · [[github wikis in obsidian & interwikilinks]] · [[renaming notes breaks links]] · [[submodule wikilink clashes]] · [[wikilink temporal integrity]] · [[note linking duplicate source]] · [[note-link-janitor]] · [[age links]] · [[Link strength]]
