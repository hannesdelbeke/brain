---
tags:
  - technical
  - obsidian
  - search
  - pkm
---
A day of work on the search engine and the Obsidian plugin over it, following [[2026-08-27 vault index work log]]. The theme is the edge nobody wrote: the index has always known which notes are close in meaning, and today that became a route, a graph view, a worklist of missing links, and one feature measured and thrown away. Written so a later session can pick up without rereading the transcript.

## The whole corpus as a graph, in one route

`GET /graph?k=` returns every note as a node and every mutual nearest-neighbour pair as an edge, with the wikilinks merged in and marked. Mutual kNN is the rule that draws: plain kNN at k=10 gives 24,132 edges over 2,959 notes and reads as a hairball, mutual kNN gives 5,458, which is the density of the 6,506 wikilinks that already exist. 1,708 of those mutual edges also carry a link, so 69% of them are pairs nobody wrote.

The payload is a path list plus `[source, target, score, linked]` indexing into it, 0.32 MB for the whole corpus against roughly four times that for edge objects carrying paths. It costs 0.15s to build, 371ms on the first HTTP call including the matrix load, and nothing after that: it is cached on the index version, so the cache clears when a reindex moves the vectors and not before.

Note vectors are the renormalised mean of the note's section vectors, which is the pooling `/similar` already uses, so no new storage and no second definition of what a note is close to. Measured and argued in [[2026-08-30 a semantic graph over the whole vault]].

## The graph view, ranked last and built anyway

The ranking in [[2026-08-30 what else the index can answer]] put a whole-vault picture sixth of six, on the grounds that it gets opened once. It was built because the route made the rest a day: a canvas rather than SVG, so 3,000 notes is one draw call instead of 13,000 DOM elements, and a Fruchterman-Reingold layout with grid-bucketed repulsion, which is O(n) a step instead of O(n²).

Layout cost by node count: 45ms at 100, 116ms at 300, 237ms at 1,000, 986ms at 2,960. So the default is a 300-node budget around the open note, widening breadth-first with the closest edge taken first, and the whole corpus is a button. Truncation keeps the highest-degree nodes, because a graph cut to whatever the path order happened to be reads as dust while one that keeps its hubs still reads as the same shape.

Solid edges are links, dashed edges are the index's, and an edge can be both. That distinction is the whole reason to draw it: overlay both without separating them and nobody can read the result.

## Missing links, which cost a filter

The same payload answers the feature that ranked first: the pairs each of which is in the other's nearest ten with no link either way, sorted by similarity, top 200. 3,750 of them on this corpus, with a 95% hit rate over a sample of the top 20.

No route was needed. The plugin already caches `/graph` for its views, so this is a filter on `linked == 0`, a sort, and a `!` prefix in the search modal — 5ms, against the `/missing` endpoint the proposal asked for. Obsidian's own link map is subtracted as well as the index's, or a link written since the last indexing pass reads as missing.

The top of the list is near-duplicate pairs rather than missing links, which is the duplicate-detection feature arriving early and unasked. It sits third in that ranking and stays there.

## Co-retrieval measured, then dropped

The query log records what comes back together, and the plan was to add that weight to the fused score. The evaluation ran before the wiring, which is the point of ranking it second rather than building it, and it said no: no bonus weight moves nDCG@10 by more than 0.02, the sign of the effect flips between neighbouring weights, and the best of 21 cells tried has p(Δ>0) of 0.89, which is what ten questions give by chance.

The reason is upstream. 97% of the query log is machine traffic — one benchmark query run 2,870 times is 49% of all pair mass, and the whole 8,338-row log touches 310 of 3,081 notes. The 4,884 associations an earlier pass counted are mostly that one query. Full measurement in [[2026-08-30 co-retrieval edges do not improve ranking]].

Two defects came out of it. A search over several corpora was logging one row naming the corpus as both names joined by a comma, so 1,227 edges landed in a bucket no single-corpus reader matches and pairs could span two corpora; the daemon now writes one row per corpus holding only that corpus's paths, with a test. And `eval_rerank.py` reports precision@limit, which is invariant under reordering: its headline metric cannot see the rerank it exists to judge. That one is recorded, not fixed, because the LLM judge it needs is not running anywhere.

## The plugin against the submission rules

The plugin was read against the current Obsidian developer docs and the rules in `obsidianmd/eslint-plugin`. Five blocking gaps, of which four are now closed: an MIT `LICENSE`, `minAppVersion` raised from 1.4.0 to 1.7.2 because `revealLeaf` is `@since` 1.7.2 with `versions.json` matched, `getBacklinksForFile` replaced by a scan of `resolvedLinks` both ways because it is not in the public API, and American spelling in the manifest description and every user-visible string. The fifth is a GitHub release, which is not mine to publish.

Two real bugs came out of the same read. The canvas font was being set to `11px var(--font-interface, sans-serif)`, and canvas discards a font string it cannot parse rather than resolving the variable, so every graph label was rendering in the 10px default; the theme variable is now read first and the resolved name goes in. And the views were reading timers, computed styles and the pixel ratio off the main window, which is the wrong window for a pane dragged into a popout.

The review also confirmed the two deliberate deviations are defensible and disclosed: the daemon is spawned detached on purpose so it outlives Obsidian and keeps serving the CLI, and Node `http` is used instead of `requestUrl` because the daemon rejects the renderer's `Origin` header, which is what makes the plugin desktop-only.

## The repository link graph, finally run over something real

`index_repo.py` had been run over exactly one repository, which had three markdown files and no relative links, so it produced 0 edges and proved nothing. Obsidian's own two documentation repositories are the test it needed: `obsidian-developer-docs`, 1,360 files, and `obsidian-help`, 11,142 files across 37 languages with 4,457 images.

The first run resolved 3 references out of 5,586. The docs are generated by API Documenter, which writes links without the extension — `[Component](Component)` — and the resolver only ever tried the path as written. Trying the same name with `.md` appended took it to 4,699.

The next layer was ambiguity. A generated API tree names the same page at several depths: four files called `workspace.md`, so `[Workspace](Workspace)` from a member page resolved to nothing, because the rule was "resolve a bare name only when exactly one file carries it". It now picks the candidate sharing the longest path prefix with the source, then the one written in the same case, then the shallower path, since `Foo/bar.md` is a member of `Foo.md` and not the reverse. All three tying still leaves it unresolved, because a wrong edge is worse than a missing one. 97.3%.

The help repository then exposed the bigger gap: 6,357 documents produced 803 edges, because it writes almost every reference as `[[page]]` or `![[image.png]]` and the repo scanner only read markdown links, embeds and bare paths. A documentation repository is often an Obsidian vault, so wikilinks are now one of the reference kinds. 803 edges became 60,223, at 94.6% resolved.

That is what makes the queries the scanner exists for answerable. "Which images are referenced by nothing" over the help repository returns 729 of 4,457, spot-checked against grep and correct, where before the fix it returned 1,533 and was measuring the parser rather than the repository.

The 150 references still unresolved in the developer docs are worth keeping: most are `[(constructor)](Foo/(constructor))`, where the link regex stops at the nested bracket, and a handful are genuinely broken links in Obsidian's published documentation, which is the feature working.

## A second scanner, over a format with no schema

The `collect=` contract had one implementation, which makes it an interface and not a seam. The second one is `index_agy.py`, over Antigravity CLI conversations, and it was chosen because it shares nothing with the first except the return type.

Nothing about the format is documented. The store was found by reading strings out of `agy.exe`: `~/.gemini/antigravity-cli/conversations/<uuid>.db`, one SQLite database per conversation, whose `steps` table holds a binary protobuf payload with no `.proto` published anywhere. So there is no line to count and no byte to resume from, which is precisely what the first scanner is built around.

The payload is read by walking wire format directly. A varint key carries the field number and the wire type, and the ambiguous case is length-delimited: a nested message, a string and a byte array are the same three bytes of header. It is parsed as a message when it parses as one and kept as a string when it decodes as printable UTF-8, and when it does both, both are kept, since a JSON argument blob parses as a message by coincidence often enough to lose it that way.

That leaves the question of which field holds what, which was answered by volume rather than by guessing: rank every field path by how many characters of text it holds across every conversation, per step type, and read the samples. Step type 14 is the user and its prose sits at `19.2`, step type 15 is the assistant at `20.1`, step type 17 is a provider error, and the rest are tool machinery. Both turns are repeated under a second path, `19.3.1` and `20.8`, so identical strings within a step are collapsed before anything is emitted.

Only the prose is taken by field number. Tool calls are found by content instead: agy writes their arguments as a JSON object, and a JSON object stays recognisable wherever the field numbers move. That matters because the field map is the fragile part, and it is the part `--probe` exists to recheck — it prints the ranked map with a sample of each field, which is how the mapping was read in the first place.

The exclusions carry over unchanged, and for the same reasons: tool results, whole-file arguments like `CodeContent`, and the assistant's thinking at `20.3`. What is kept is prose plus a whitelist of arguments, and the ones naming a path become edges.

Resume is a cursor rather than an offset. Each conversation records the highest `steps.idx` it read, and the next run reparses from that index rather than past it, because agy rewrites the last step in place while the answer streams. The rows before it come back out of the index through `index_sessions.cached_rows`, which turned out to be source-agnostic already.

One bug worth recording. A section id was `path::step:chunk`, and a single step can hold both an assistant turn and the tool call it made, so the second silently overwrote the first through its primary key: the run reported 1,511 sections and the database held 1,464. The id carries the event index now, and the selfcheck asserts the ids are unique.

Measured over 18 conversations and 44 MB: 17 notes, 1,511 sections, 107 edges, 2.4 MB of index, 0.83s cold and 0.26s of scan on a resume. The eighteenth was one `/usage` and produced no prose, which is the correct answer. Searched through the daemon over `--corpus` with no code of its own, which is the actual proof.

Eighteen conversations is not enough to trust a hand-read wire format, so `index_agy_validation.md` sits beside the scanner: eight steps with a pass rule and a failure signature each, written for an agent to run unattended on a machine with hundreds, and a report template that asks for numbers.

## Where it stands

Five surfaces over one daemon client: the search modal with five prefixes, the related pane, the semantic local graph, the vault graph, and missing links. 76 tests against a fake Obsidian and a fake daemon, plus a live suite that drives the same views against the running daemon and is the only thing that catches a route changing shape. Live timings over 2,961 notes: related pane 177ms, local graph 31ms, vault graph 672ms around a note, 1,033ms for the whole corpus, missing links 4ms.

Engine side: 48 tests, and the daemon was restarted onto the current code and checked, since a daemon running yesterday's file is the failure that hides every fix.

## Open

Nobody has looked at any of this inside Obsidian. Every number above comes from a harness, including the label fix, which by definition was never seen.

The plugin repository is private and has no release, and submission needs both. The manifest author is "Claude" while the directory verifies ownership against the GitHub account, so the listing would show a name matching neither.

The superseded `semantic-local-graph` prototype is still in this vault's plugin directory, untracked, and deleting it is not recoverable.

Further reading: [[2026-08-29 one obsidian plugin over the search daemon]] for what the plugin is and why it is one plugin rather than four, [[2026-08-29 local search daemon and indexer - release plan and modular decoupling]] for how the pieces get distributed, and [[2026-08-30 one daemon, several agents asking at once]] for the concurrency work whose benchmark loops polluted the query log measured above.
