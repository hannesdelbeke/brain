---
date: 2026-08-30
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
> the obsidian side of the local search engine: backlinks, unlinked mentions, semantic neighbours and search, as one plugin rather than four, all of them reading from the daemon that already runs.
> the merge happened on 2026-08-30 and the plugin exists: three surfaces, one daemon client, 45 tests against a fake obsidian and a live test against the real daemon. what is left is a look at it inside obsidian, and the measurement that decides whether the backlinks pane is worth keeping at all.
> **needs from you:** open the private vault and look at the three surfaces, since nothing below has been seen by a human in the app yet.

> so if i want fast backlink search in obsidian, and semantic search later, and we have a prototype plugin in the vault, what are the next steps. and does it make sense to make separate plugins, backlinks, search, semantic search, semantic backlinks

> [!todo] next
> **next:** open the private vault in obsidian and use the three surfaces, since every measurement below is from a test harness and nothing has been seen rendered.
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

## what shipped on 2026-08-30

one plugin, `unified-search` in the private vault and `h-forts/obsidian-unified-search` as its repository, still plain javascript with no build step. three surfaces over one daemon client: the search modal, a related pane holding linked mentions, unlinked mentions and semantic neighbours as three sections, and the semantic local graph. the related pane fires its three routes in parallel and only `/links` is required, so a corpus with no vectors still renders backlinks.

driven from a test harness against the running daemon, one note in the 871-note private corpus: the related pane renders in 107ms for all three sections, the graph in 22ms, a semantic query through the modal in 252ms, and a note the index has never seen still draws neighbours in 223ms through the `/search` fallback. the 2.7s first-call cost is gone from the interactive path, paid instead by one throwaway `/similar` after layout is ready.

six bugs were in the two prototypes and none of them would have been visible as a crash. the modal searched whichever corpus the daemon happened to default to, because it never sent a vault and never resolved one, which is the wrong-corpus failure of 2026-08-28 arriving through a third door. it also spawned the daemon with no `--vault`, so an autostart registered whatever obsidian's working directory resolved to. a failed spawn left a latch set and no further attempt was possible for the session. a slow semantic round trip could overwrite the results of a newer keystroke. the graph threw on a result with no score, and its debounce timer outlived the view while its cache grew without limit.

the corpus is now resolved by matching this vault's own path against the roots in `/health`, rather than by a name typed into settings, which is the fix that generalises: a client that names its corpus by hand is a client that will one day name the wrong one.

## how it is tested without obsidian

`harness.js` intercepts `require("obsidian")` before `main.js` loads and hands it a fake: `Plugin`, `ItemView`, `SuggestModal`, `Setting`, a DOM stub whose `createEl` records a tree that assertions can read, and a fake daemon that is a real HTTP server serving the shapes `searchd.py` returns, including its 200-with-an-error-field case. so the views, the modal and the settings tab run for real, rather than only the pure functions being reachable, which is all the two prototypes' tests could touch.

45 tests, and they were checked by breaking the code: five deliberate mutations, five failures, one of which exposed a test that was passing for the wrong reason. `test-live.js` runs the same views against the daemon that is actually running, which is the only thing that catches a route quietly changing shape.

## what is left

1. use it in obsidian. nothing here has been seen rendered.
2. measure native backlinks before keeping the linked-mentions section, which is the section below.
3. a `build` script and a minified `main.js`, needed only if this is submitted, see the release plan.
4. leave the python alone. the primitive split, `--no-vectors` and any packaging are on the distribution path, not on this one.

## measure before replacing native backlinks

obsidian answers backlinks from an in-memory cache, and at 3,283 notes that is plausibly faster than a 30ms round trip. the honest case for this pane is not speed, it is the two things obsidian has no answer for: unlinked mentions that exclude code blocks and frontmatter, and semantic neighbours as soft backlinks beside the hard ones.

the measurement is available rather than hypothetical, since [[2026-08-29 Startup Metrics Logger devlog]] shipped the instrument. take the native number first; if it is fast, drop the replacement and keep the two panes that add something.

one thing the endpoint check turned up: inbound edges carry raw targets like `public/pkm-search|pkm-search`, the path-prefixed wikilinks. they resolve while the private vault is the obsidian root and break the moment this vault is opened on its own, so a backlinks pane will render them correctly and quietly depend on a layout that is not guaranteed.

the acceptance for each feature this replaces is listed in [[core Obsidian features to rework on the vault index]], the corpora the daemon answers over are in [[corpus]], and the submission path, once any of this is worth publishing, is [[2026-08-29 Obsidian community plugin submission process]].
