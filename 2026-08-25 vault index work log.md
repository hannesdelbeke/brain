---
tags:
  - technical
  - obsidian
  - search
  - pkm
---
A day of work on the vault index, run mostly by agents in parallel. This note is the overview; each item links to the note that holds the detail. Written so a later session can pick up without rereading the transcript.

## Finding work to do

The starting question was how to find unsolved problems in a vault of 3,228 notes. Semantic search answers it badly, because "problem" is a shape rather than a topic. Structure answers it well: a problem heading with no solution heading, a title starting with TODO, open checkboxes, and a small set of marker phrases. [[find_open_problems.py]] scores notes on those four signals and scans the vault in about 2 seconds without touching the index, so it works when the index is stale. See [[finding unsolved problems in my vault]].

A note is retired from the list by adding `solved` to its frontmatter tags, which zeroes its score. The open count went from 117 to 109 over the day. Twenty-six notes were tagged in the sweep.

Two ranking tools came out of the same question. [[urgent_tasks.py]] ranks open tasks, and [[mention_heatmap.py]] scores link targets by `0.5 ** (age_days / 30)` per distinct day mentioned, read from `git log -p` rather than the `edges` table, because `edges` holds the current graph with no dates and in-degree just ranks hubs. See [[Priority heatmap]] and [[TODO how to highlight urgent tasks]].

## Notes solved

[[fix issues in my mkdocs wiki]] closed as will-not-do, with the reason recorded rather than the note deleted. [[Obsidian plugin - Excalidraw]] closed. [[hierarchical map-reduce note rollup]] got a full design and the conclusion not to materialise the tree.

## Daemon endpoints added

`GET /unlinked?note=` serves unlinked mentions from the index instead of Obsidian's own pane, with four exclusions the pane gets wrong, including matches inside code fences. 20 to 48ms in the daemon at `limit=20`. See [[unlinked mentions from the vault index]] and [[Obsidian unlinked mentions include code snippets]].

`GET /similar?note=` answers "nearest notes to this note". `/search` spends about 220ms encoding the query string on the CPU provider, which is most of the cost of a call and pure waste for a note that is already indexed. `find_similar_notes` mean-pools the note's own section vectors, normalises, and multiplies the resident matrix, so no model runs: 11 to 26ms over HTTP at `limit=36`, against 228 to 541ms for the same note through `/search`. The response shape matches `/search`, so a caller only changes the URL, and an unresolvable note returns an error rather than an empty list, which is how a caller decides whether to fall back.

## Obsidian features worth rebuilding on the index

[[core Obsidian features to rework on the vault index]] lists six, each as a task callout with related notes attached. The rule for picking a candidate is that the built-in does a linear content scan, or matches on titles only. Measured while writing it: 3,228 notes, 2,185 with inbound links, 1,043 orphans, 1,780 unresolved edges.

## Semantic local graph plugin

Built and installed at `.obsidian/plugins/semantic-local-graph`, plain `main.js` with no build step, unit tests in `test.js`. It draws the active note's semantic neighbours in the right sidebar: solid edge where a wikilink already exists, dashed where the relation is semantic only, distance from centre encoding similarity. It calls `/similar` and falls back to `/search` for a note written since the last reindex, caches per note keyed on mtime, and debounces leaf changes.

It does not lag on a large vault because it never draws one. A fixed node budget with a static radial layout, no force simulation and no animation frame, means redraw cost is independent of vault size. The global graph problem is not solved here, it is avoided; no plugin credibly makes a 10k node global graph fast, and past a few hundred notes that view is a poster rather than a tool.

A survey of what already exists came back build rather than install. Smart Connections, Smart Related Notes, 3D Semantic Graph, Graphene and Neural Composer all build a second embedding index inside the renderer, paying twice for vectors that already exist. Semantic Linker is closest by shape, a semantic local graph in the right sidebar pointed at a local endpoint, but it embeds titles, tags and frontmatter only, so it cannot connect two notes that say the same thing in different words, which is the whole point. Ideas worth taking later: a ranked list beside the graph, a similarity floor as its own setting alongside top-k, and path exclusion for the journal folder, which will dominate semantic neighbours the way it dominates the graph.

## Concept note

[[semantic index as a git extension]] works out what it would take to install a semantic index into any git repository the way `git lfs install` does, including rollup and the other search optimisers, and how to describe binary blobs such as images and meshes in LFS. Prior art is thin but not empty. The load-bearing findings: only the `.gitattributes` line travels, everything else is written by a local install step; a vector keyed by blob SHA is rename-proof and dedups across repos for free; a directory's tree SHA is the rollup invalidation DAG that the vault design had to reject; and committing the index is a mistake that every mainstream tool independently declined to make.

## Open

The plugin lives under `.obsidian/`, which this repository ignores, so it is not pushed with the rest. Moving it to its own repository is the obvious fix if it is worth keeping.

`/unlinked` has no plugin calling it yet. The daemon needs a restart to pick up either new endpoint, since routes are loaded at start.

## Related
- [[vault hybrid search]] — the query path both endpoints sit on
- [[lightning-fast unified search plugin for obsidian]] — the daemon and the plugin pattern reused here
- [[Obsidian core plugin]] — which built-ins exist to be reworked
- [[PKM indexer performance log]] — the measured numbers this note quotes against
- [[codegraph review]] — the same job on source rather than notes
