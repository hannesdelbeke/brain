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
> obsidian's graph draws the links you wrote. the index knows a second kind of edge, the notes that are close in meaning whether or not you ever linked them, and this is what a graph over all of them looks like once it is measured rather than imagined.
> mutual nearest neighbours is the version that draws: 5,458 edges over 2,959 notes, about the size of the wikilink graph, where plain nearest-neighbours gives 24,132 and a hairball. 69% of those edges are pairs you never linked, which is the whole point and also the reason the view has to be readable.
> **needs from you:** nothing. the `/graph` route shipped on 2026-08-30 and the view is being built on top of it.

> with the index and the daemon we have more connections. remake the obsidian graph but more optimised and with semantic connections

> [!todo] next
> **next:** the view. the route is written, the layout is not.
> **blocked:** nothing.

**why:** [[2026-08-29 one obsidian plugin over the search daemon]]

## what the index can already draw

every section has a vector. a note vector is the mean of its section vectors, renormalised, which costs one pass and no new storage. from there the whole-vault question is one matrix multiply, and the numbers below are from running it over 2,966 notes.

| edge rule | edges | reads as |
| --- | --- | --- |
| every pair over a similarity cutoff | tuning exercise | a cutoff that is right for one cluster is wrong for the next |
| k nearest neighbours, k=10 | 24,132 | a hairball, every note has ten edges whether or not it deserves them |
| mutual kNN, k=10 | 5,458 | comparable to the 6,506 wikilinks that exist |
| the wikilinks themselves | 6,506 | what obsidian draws today |

mutual kNN is the rule worth shipping: an edge exists when each note is in the other's top ten, so a hub note stops attaching itself to everything and a note nobody is near keeps no edges at all. it also lands, without tuning, at about the density of the hand-written link graph, which is a good sign that the resulting picture is legible.

**1,708 of the 5,458 mutual edges also carry a wikilink, so 69% of them are new.** an earlier pass over this said 87%, from a wikilink set that was counted per direction rather than per pair; the corrected number is the one to use. it is still the feature and the warning in one: the semantic graph is not a prettier version of the link graph, it is mostly new information, and a view that overlays both without distinguishing them is a view nobody can read.

drawn together, the public corpus is 2,959 nodes and 10,256 edges: 1,708 pairs that are both near and linked, 3,750 near only, 4,798 linked only. mean degree 7.1, maximum 102, and 58 notes with no edge of either kind.

## what does not work, measured rather than assumed

projecting the 384 dimensions down to two and using position as meaning does not survive contact with the data. taking each note's five nearest neighbours in the full space and asking how many are still among its five nearest on the map: PCA keeps 0.11 of 5, spectral 0.34 of 5. the map looks like a map and is noise. so position must come from a force layout over the edge list, where the edges are the truth and the coordinates are only a way to see them, exactly as obsidian already does.

the payload is not the problem: 5,519 edges is 0.18 MB of JSON and about 140ms warm. the drawing is the problem, and it is the same drawing problem obsidian already solved once.

## so the honest scope

the local graph, one note and its neighbours, already ships and is the version that earns its cost every day: bounded node count, no layout beyond a radial sort by similarity, redraws in tens of milliseconds. a whole-vault view is a different feature with a different failure mode, which is that it is beautiful once and never opened again.

if it is built, the shape is: a `/graph` route returning `{nodes, edges}` for a corpus, computed once and cached on the index version so it is free until the index changes; a canvas rather than SVG past a few thousand nodes; and a filter that starts from the open note's neighbourhood rather than from everything, because "everything" is the view that gets opened once.

the route shipped on 2026-08-30, 60 lines. `nodes` is a path list and an edge indexes into it, `[source, target, score, linked]`, which is 0.32 MB of JSON for the whole public corpus where the same edges written out as objects with paths in them are four times that. building it costs 0.15s, the first call over HTTP measured 371ms including the matrix load, and every call after it is served from the cache until the index moves.

## the features next to it, ranked by what they give per hour spent

1. **freshness.** the pane answers out of the index, so a note edited since the last pass gets answers that are behind. `/health` already carries when the pass finished. *shipped on 2026-08-30, with a reindex the user can click.*
2. **the other corpora.** one daemon serves several indexes, and no other obsidian plugin can show you the note in your other vault that is about what you are writing now. `/similar` cannot cross an index, so it is `/search` over the note's own text with the vault parameter set to all. *shipped the same day, off by default, 1.7s against two corpora.*
3. **missing links.** the pairs that are mutual nearest neighbours and are not linked, sorted by how close they are, is a list of specific edits rather than a picture. it is the mutual-kNN computation above with the wikilinks subtracted, which is why the graph work pays for it.
4. **section-level related.** neighbours of the paragraph the cursor is in rather than of the whole note. the sections are already the unit the index stores, so this is a route parameter and a heading, and it is the one that changes what writing in the editor feels like.
5. **the whole-vault graph.** the picture. last, because it is the most work and the least likely to be opened twice.

related: [[2026-08-29 local search daemon and indexer - release plan and modular decoupling]] for where the python lives, [[core Obsidian features to rework on the vault index]] for the acceptance each replaced feature needs, and [[2026-08-18 what retrieval costs as a vault grows]] for why the answers are locations rather than bodies.
