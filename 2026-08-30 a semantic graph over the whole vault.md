---
date: 2026-08-30
created: 2026-08-30
tags:
  - obsidian
  - graph
  - search
  - embeddings
  - pkm
---

> [!summary] eli5
> obsidian's graph draws the links you typed. the search index knows a second kind of connection: notes that mean similar things, whether or not you ever linked them. this note is that second graph, measured and then drawn.
> the rule that produces a readable picture is mutual nearest neighbours: 5,458 connections over 2,959 notes, about the same density as the 6,506 links already in the vault. the obvious rule, "each note connects to its ten closest", gives 24,132 and a hairball.
> 69% of the semantic connections are pairs you never linked. that is the value and the risk in one: it is mostly new information, so the view has to keep the two kinds apart or it is unreadable.
> **needs from you:** open obsidian and look at it. the route, the view and the missing-links list all shipped on 2026-08-30 and no human has seen any of it rendered.

> with the index and the daemon we have more connections. remake the obsidian graph but more optimised and with semantic connections

> [!todo] next
> **next:** a human looks at the surfaces in obsidian and says which are worth keeping.
> **blocked:** nothing.

**why:** [[2026-08-29 one obsidian plugin over the search daemon]]

## the raw material

the index already stores a vector for every `##` section of every note. a note's vector is the average of its sections' vectors, rescaled to unit length. that is the same averaging `/similar` has always used, so there is no new storage and no second definition of what a note is about.

with one vector per note, "how close is every note to every other note" is a single matrix multiply. over 2,966 notes that is 4.4 million pairs and takes a fraction of a second. the question is not whether the numbers exist. it is which of those 4.4 million pairs deserve a line drawn between them.

## which pairs get a line

| rule | connections | what it looks like |
| --- | --- | --- |
| every pair above a fixed similarity score | depends entirely on the number | a threshold that suits one cluster is wrong for the next |
| each note connects to its 10 closest | 24,132 | a hairball. every note gets ten lines whether it deserves them or not |
| mutual: both notes are in each other's 10 closest | 5,458 | comparable to the links already written |
| the wikilinks you typed | 6,506 | what obsidian draws today |

mutual nearest neighbours is the rule that shipped. a line exists only when the feeling is returned: note A is in B's ten closest **and** B is in A's ten closest. two things fall out of that for free.

a hub note stops attaching itself to everything. a note about "obsidian" is near hundreds of notes, so under the plain rule it collects hundreds of lines. under the mutual rule it keeps only the notes that also consider it one of their own closest, which is the handful actually about obsidian rather than merely mentioning it.

a note nobody is near keeps no lines at all. under the plain rule every note has exactly ten, including the ones with nothing to connect to, which is how you get lines that mean nothing.

there is no threshold to tune, and the density it lands on is close to the hand-written link graph without anyone aiming for that. that is a decent sign the picture will be legible, since the link graph is a density a human already reads.

## how much of it is new

1,708 of the 5,458 mutual connections also carry a wikilink. so 69% of them are pairs nobody linked.

an earlier pass reported 87%. that came from counting wikilinks per direction instead of per pair; 69% is the number to use.

drawn together, the public corpus is 2,959 notes and 10,256 connections:

- 1,708 pairs both near in meaning and linked
- 3,750 pairs near in meaning only, which is the missing-links list further down
- 4,798 pairs linked only, which is everything from a passing mention to a link written for a reason the vectors cannot see

mean connections per note is 7.1, the most connected note has 102, and 58 notes have none of either kind.

the practical consequence: this is not a prettier version of the graph obsidian already draws. two thirds of it is information the link graph does not contain, so a view that mixes the two without telling them apart is a view nobody can read. in the drawing, a link you wrote is a solid line and a connection the index found is dashed.

## why the map cannot come from the vectors

the tempting shortcut is to squash the 384 numbers per note down to two and use those as x and y on screen. then position means something and no layout algorithm is needed.

it does not survive being checked. take each note's five nearest neighbours in the full 384 dimensions, then ask how many of those five are still among its five nearest on the flattened map:

- PCA keeps 0.11 of 5
- spectral embedding keeps 0.34 of 5

so roughly 2% and 7% of what you would be looking at is real. the map looks like a map and is noise. anyone reading clusters off it is reading an artefact of the projection.

position therefore comes from a force layout over the connection list, the same as obsidian does it. the connections are the truth, and coordinates are only a way to see them. two notes ending up near each other on screen is a hint, not a measurement.

## the route

`GET /graph?k=10` returns the whole corpus as `{nodes, edges}`. it shipped in about 60 lines of python.

`nodes` is a plain list of paths. an edge is `[source, target, score, linked]`, where source and target are positions in that list. writing edges as objects with the paths spelled out costs four times as much: the compact form is 0.32 MB of JSON for the whole public corpus.

building it takes 0.15s. the first HTTP call measured 371ms including loading the vector matrix from disk. every call after that is served from a cache keyed on the index version, so it is free until a reindex moves the vectors, and stale by construction never.

one route feeds three separate features, which is why it was worth building before deciding whether the picture itself was a good idea.

## the view

canvas, not SVG. the whole corpus is 2,959 notes and 10,256 lines, which is roughly 13,000 DOM elements against one draw call per frame.

layout is Fruchterman-Reingold: connected notes pull together, all notes push apart, the step size cools over the run. the push is the expensive half, since done naively it compares every note against every other. instead notes are bucketed into a grid whose cells are the length of an ideal edge, and each note is only pushed by the nine cells around it. that makes a step linear in the number of notes rather than quadratic. a quadtree would restore the long-range push, and it only starts to matter past ten thousand notes.

what you get on screen:

- a dot per note, sized by how many connections it has, with the open note enlarged and highlighted
- solid lines for links you wrote, dashed for connections the index found
- names appear as you zoom in past 1.6x, and before that only the open note and whatever the pointer is over are named
- scroll to zoom about the pointer, drag to pan, click a dot to open the note
- two buttons: "around this note" versus "whole corpus", and "rebuild"
- a caption under the canvas saying how many of the total notes and connections are being drawn

## how big before it slows

| notes drawn | layout time |
| --- | --- |
| 100 | 45ms |
| 300, the default | 116ms |
| 1,000 | 237ms |
| 2,960 | 986ms |

so the default budget is 300 notes and the whole corpus is a button, not the landing state.

when the budget is smaller than the vault, which notes survive depends on the mode. around the open note, it widens outward in rings, always taking the strongest connection first, so the budget buys the notes surrounding this one rather than one long chain leading away from it. in whole-corpus mode it keeps the most connected notes first, because a graph cut down to whatever order the file paths happened to be in reads as dust, while one that keeps its hubs still reads as the same shape.

the payload was never the bottleneck. drawing was, and it is the same drawing problem obsidian already solved once.

## missing links, the version without a picture

the same data, minus the picture: every pair that is mutually near with no link either way, sorted by how close they are. 3,750 of them on the public corpus, and the top 200 are kept, because the hit rate falls off in the tail and this is a worklist rather than an inventory.

it cost no new route. the plugin already holds the `/graph` payload for its views, so this is a filter on the `linked` flag, a sort, and the `!` prefix in the search modal. 5ms.

obsidian's own link map is subtracted as well as the index's flag. the index is always at least one pass behind the vault, so without that a link written five minutes ago still reads as missing.

sampling the top 20 by hand: 19 are pairs that should be linked, one is unclear, none are wrong. the very top of the list is near-duplicate notes rather than missing links, which is the duplicate-detection feature showing up early and uninvited.

a list of specific edits beats a picture, which is why this ranked first of the features below and the picture ranked last.

## what shipped, in the order it was worth doing

1. **freshness.** the panes answer out of the index, so a note edited since the last pass gets stale answers. `/health` already reports when the pass finished, so the view says so and offers a reindex button. *shipped 2026-08-30.*
2. **the other corpora.** one daemon serves several indexes, and no other obsidian plugin can show you the note in your other vault that is about what you are writing now. `/similar` cannot cross an index, so it runs `/search` over the note's own text with the vault set to all. *shipped the same day, off by default, 1.7s against two corpora.*
3. **missing links.** the section above. *shipped, 5ms, top 200 of 3,750.*
4. **section-level related.** neighbours of the paragraph the cursor is in, rather than of the whole note. sections are already the unit the index stores, so this is a route parameter and a heading. *not built.* it is the one most likely to change what writing in the editor feels like.
5. **the whole-vault picture.** *shipped out of order, because the route made it a day of work rather than a week.* the reservation stands: a picture of everything is the feature that gets opened once. whether it gets opened twice is a question only use answers.

related: [[2026-08-30 what else the index can answer]] for the five candidate features this ranking came from, [[2026-08-30 vault index work log]] for the day it was all built, [[2026-08-29 local search daemon and indexer - release plan and modular decoupling]] for where the python lives, [[core Obsidian features to rework on the vault index]] for the acceptance each replaced feature needs, and [[2026-08-18 what retrieval costs as a vault grows]] for why the answers are locations rather than bodies.
