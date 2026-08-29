---
date: 2026-08-29
created: 2026-08-29
tags:
  - obsidian
  - search
  - plugin
  - architecture
  - pkm
aliases:
  - one obsidian plugin over the search daemon
---

> [!summary] eli5
> the plan for the obsidian side of the local search engine: backlinks, unlinked mentions, semantic neighbours and search, as one plugin rather than four, all of them reading from the daemon that already runs.
> nothing new is needed in the engine, the three endpoints these features need already answer in tens of milliseconds; what exists is two prototype plugins that each carry their own copy of the daemon client, and the work is merging them before a third copy appears.
> **needs from you:** nothing to decide, the first step is a merge of code you already have; the measurement in the last section decides whether the backlinks pane is worth shipping at all.

> so if i want fast backlink search in obsidian, and semantic search later, and we have a prototype plugin in the vault, what are the next steps. and does it make sense to make separate plugins, backlinks, search, semantic search, semantic backlinks

> [!todo] next
> **next:** merge `unified-search` and `semantic-local-graph` into one plugin with a single shared daemon client file, since each carries its own copy today and the backlinks pane would be the third.
> **blocked:** nothing.

**why:** [[2026-08-29 local search daemon and indexer - release plan and modular decoupling]]

## the engine side is already done

measured against the running daemon on 2026-08-29, one note in a 3,283-note corpus, over curl, so each number carries about 15ms of process startup that an in-process fetch does not pay:

| endpoint | what it returns | measured |
| --- | --- | --- |
| `/links?note=` | inbound and outbound edges with line numbers, 24 inbound for `pkm-search.md` | 28 to 42ms |
| `/unlinked?note=` | unlinked mentions from FTS5 | 70 to 270ms |
| `/similar?note=` | nearest notes in embedding space | 40ms warm, 2.7s on the first call |

so fast backlinks needs no python written, no index change and no packaging. it needs a view that renders `/links`. that is the whole gap.

the 2.7s is the corpus vector matrix loading on first use, which the keepalive does not cover because keepalive keeps the model warm and not the matrix. one throwaway `/similar` when the plugin loads turns the first semantic hover from 2.7s into 40ms.

## one plugin, not four

backlinks, search, semantic search and semantic neighbours all need the same thing: a python daemon on `127.0.0.1:44771`. there is no reader who installs the backlinks one and not the others, because the install cost is the daemon and it is paid once for all four.

four plugins would mean four copies of the daemon client, four settings tabs, four connection indicators, four things that fail identically when the daemon is down, four community submissions and four rows in a plugin list that is already being measured for startup cost. inside one plugin each feature is a toggle and a lazily created leaf.

the split that would matter is daemon or no daemon, and none of these four sit on the no-daemon side.

## what exists, and the copy to remove first

`unified-search` in the private vault's `.obsidian/plugins/`, extracted to `h-forts/obsidian-unified-search`, 395 lines of plain javascript with no build step: a modal with fuzzy, regex, tag and date modes, and semantic delegating to the daemon.

`semantic-local-graph` in this vault's `.obsidian/plugins/`, 413 lines: a local graph of the notes nearest in meaning to the open note, drawing a fixed number of nodes so it does not slow down as the vault grows.

both hold their own base URL, their own fetch, their own CLI fallback, their own python discovery and their own spawn of the daemon when it is not running. that duplication is the same failure the engine already paid for as two published python copies, and the backlinks pane is where it becomes a third. merge first, add the pane second.

## the steps

1. merge the two plugins into one, with the daemon client as a single file both views import. no typescript and no bundler unless something needs them; two working plugins in plain javascript are evidence that neither is needed yet.
2. add the backlinks leaf against `/links`, inbound and outbound, each row a jump to its line since the endpoint already returns them.
3. warm the vector path on plugin load with one `/similar` call.
4. add unlinked mentions from `/unlinked` behind its own toggle, since at 70 to 270ms it is slower than the other two and should not sit in the same render pass.
5. leave the python alone. the primitive split, `--no-vectors` and any packaging are on the distribution path, not on this one.

## measure before replacing native backlinks

obsidian answers backlinks from an in-memory cache, and at 3,283 notes that is plausibly faster than a 30ms round trip. the honest case for this pane is not speed, it is the two things obsidian has no answer for: unlinked mentions that exclude code blocks and frontmatter, and semantic neighbours as soft backlinks beside the hard ones.

the measurement is available rather than hypothetical, since [[2026-08-29 Startup Metrics Logger devlog]] shipped the instrument. take the native number first; if it is fast, drop the replacement and keep the two panes that add something.

one thing the endpoint check turned up: inbound edges carry raw targets like `public/pkm-search|pkm-search`, the path-prefixed wikilinks. they resolve while the private vault is the obsidian root and break the moment this vault is opened on its own, so a backlinks pane will render them correctly and quietly depend on a layout that is not guaranteed.

the acceptance for each feature this replaces is listed in [[core Obsidian features to rework on the vault index]], the corpora the daemon answers over are in [[corpus]], and the submission path, once any of this is worth publishing, is [[2026-08-29 Obsidian community plugin submission process]].
