---
<<<<<<< HEAD
date: 2026-08-29
=======
date: 2026-08-30
>>>>>>> 043a9802989d5522611c6a13f19ede56b31041d1
created: 2026-08-29
tags:
  - architecture
  - search
  - release-plan
  - modularity
  - obsidian
  - pkm
aliases:
  - search suite release plan
---

> [!summary] eli5
> whether the local search engine, today one directory of python inside this vault, should be split into parts and published for other people: a core library, an obsidian plugin, and a searcher over agent transcripts.
<<<<<<< HEAD
> the engine already ran as two published copies once and they drifted, so the shape of any release is generated from the one copy rather than maintained beside it; of the three packages the transcript searcher is the only one that pays for itself before anyone else installs it.
=======
> the engine already ran as two published copies once and they drifted, so the shape of any release is generated from the one copy rather than maintained beside it; of the three packages the transcript searcher is the only one that pays for itself before anyone else installs it, and the obsidian one is written but not submitted.
>>>>>>> 043a9802989d5522611c6a13f19ede56b31041d1
> **needs from you:** decide whether publishing is a goal at all, since none of this is worth doing for a single user, and the obsidian half competes with a plugin that already ships the same retrieval.

> do a pass over the release plan and modular decoupling note, written by gemini flash. check what the vault already says about decoupling into a repository, and link those notes.

> [!todo] next
> **next:** write a second transcript scanner over `~/.gemini/antigravity-cli/history.jsonl` returning the same `(notes, sections, links, errors)` tuple as `scan_sessions`, because every package below rests on the scanner seam being real and today it has one implementation.
> **blocked:** whether publishing is a goal, which decides whether anything past that scanner happens.

**why:** [[progress - local-first search daemon and indexer]]

## what is already decided

the engine was published twice, as `skills/pkm-metadata-indexer/` in this vault and as a standalone repository, and the two copies drifted across seven files until a fix landing in one did not reach the other, which is why the idle CPU fix had to be written twice. on 2026-08-27 one copy was deleted: the standalone repository is a `README.md` pointing here and consumers find the engine by path, see [[pkm-search]].

so a release plan is not choosing between one copy and several. it is deciding whether the one copy gets a distribution channel, and if it does, every artifact is generated from this directory by CI and pushed, never hand-maintained beside it. three packages hand-maintained is the drift already paid for once, three times over.

## the three primitives, and whether they need separating

extraction, lexical search and vector search are already separable in behaviour. a corpus indexed without embeddings answers from FTS5 alone, which is how the transcript corpus ran for weeks, and the vector half is a `--with-embeddings` pass that adds a float32 blob per section. what is not separated is the source: they live together in `index_pkm_meta.py`, 1,669 lines, with the daemon another 800.

so the split buys one thing that does not exist today, an install that never touches ONNX: no model download, no DirectML, no 122 MB resident matrix, for a low-power machine or a CI job or a person who will not install a model to search their notes. that is a real story, and it needs a `--no-vectors` flag and an optional dependency group more than it needs three files.

what the split does not buy is architecture. an extractor importable on its own, a lexical module and a vector module are three interfaces with one caller each until a second package imports one of them. do it when the session searcher below needs the extractor without the rest, which is the first moment the seam has a second consumer, and not before.

the section contract is worth freezing either way, since everything downstream is written against it: `(heading, start_line, end_line, content, sha256)`, with the sha256 already keying vector reuse.

## package A, the core engine

what exists: the daemon on `127.0.0.1:44771`, the `--corpus` scanner seam, section-level sha256 reuse, tail reads over append-only files, per-corpus watching, staleness reported on the query path, the opt-in cross-encoder rerank, and unit tests over the parts that fail silently. no assistant SDK is imported anywhere in it.

what a package needs that does not exist: an install that works without this vault around it, dependencies declared rather than assumed, the scanner contract documented as the supported extension point rather than as a section of a skill file, and an MCP endpoint, which is named in every plan of this shape and is not in the code today. the honest scope of the first release is a pip install, a daemon command, a query command, and the scanner contract.

sub-5ms is not a claim to publish. warm hybrid queries measure 13 to 22ms on the note corpora and 34 to 62ms on transcripts, and the first query after a cold boot waits 3 to 5 seconds for DirectX 12 driver compilation. the number worth leading with is the one that is unusual: 0.000 cores while idle, on a resident model daemon.

## package B, the obsidian plugin

a plugin already ships FTS5 plus local vectors plus reciprocal rank fusion over MCP. both engines were measured on the same 3,264 notes in [[2026-08-27 build or install, measuring the engine against the plugin that already exists]], and the prior art is surveyed in [[2026-08-27 what already exists, prior art for a local hybrid search engine]]. a plugin that leads with hybrid search is a worse version of something already installable, so if this one ships it leads with what the other does not have: several corpora in one daemon, so a vault search also reaches code repositories and agent transcripts, and the `edges` table as a first-class object.

<<<<<<< HEAD
that second part is where the interesting feature is. backlinks answered as one indexed query against `edges` instead of a linear scan, unlinked mentions from FTS5 with code blocks and frontmatter excluded, and nearest-neighbour notes as soft backlinks beside the hard ones. the specific timings a plan of this shape asserts, sub-millisecond backlinks against a twelve second native startup, are unmeasured; the startup half can be measured with the plugin already published in [[2026-08-29 Startup Metrics Logger devlog]], and until it is, the feature is a hypothesis with a benchmark attached.

the submission path is known rather than researched, written up in [[2026-08-29 Obsidian community plugin submission process]] and walked once already. what the plugin cannot avoid is the daemon: a community plugin that requires the user to install a python service is a different product from one that ships self-contained, and that is the design question to answer before writing typescript. the features worth rebuilding, with their acceptance, are listed in [[core Obsidian features to rework on the vault index]], and the plan for building them as one plugin over the endpoints that already answer is [[2026-08-29 one obsidian plugin over the search daemon]].
=======
that second part is where the interesting feature is. backlinks answered as one indexed query against `edges` instead of a linear scan, unlinked mentions from FTS5 with code blocks and frontmatter excluded, and nearest-neighbour notes as soft backlinks beside the hard ones.

as of 2026-08-30 there is a fourth, and it is the one that reads as a product rather than as a faster version of something: the graph view drawn over meaning as well as over links. `/graph` returns the whole corpus as mutual nearest neighbours plus the wikilinks, 2,959 notes and 10,256 edges over the public corpus, of which 4,798 are links nobody could draw semantically and 3,750 are pairs nobody wrote a link between. no plugin can copy that without an index of vectors and a resident daemon, which is the difference between a feature and a moat. it is measured in [[2026-08-30 a semantic graph over the whole vault]]. the same payload pays for a fifth: the missing-links list, the 3,750 unwritten pairs sorted by how close they are, which is the graph turned into a worklist of edits and which cost a filter rather than a route. the specific timings a plan of this shape asserts, sub-millisecond backlinks against a twelve second native startup, are unmeasured; the startup half can be measured with the plugin already published in [[2026-08-29 Startup Metrics Logger devlog]], and until it is, the feature is a hypothesis with a benchmark attached.

the plugin itself was built out of order on 2026-08-30, ahead of everything else in this plan, because it was a merge of two prototypes that were already drifting rather than new work, and a third copy of the daemon client was about to appear. it exists, it is tested against the running daemon, and it is described in [[2026-08-29 one obsidian plugin over the search daemon]]. building it early costs nothing here: it is the one package with no dependency on the scanner seam. the features worth rebuilding, with their acceptance, are listed in [[core Obsidian features to rework on the vault index]].

### what the directory checks now, and the two things that fail today

the submission path moved. it is a form at community.obsidian.md rather than a pull request against `obsidian-releases`, and review is an automated scan on every release, scored across manifest, releases, source code and build verification, with errors blocking installation and warnings not. the source-code half is literally `obsidianmd/eslint-plugin`, which can be run locally before submitting, and the portal will run a preview scan against a branch. the older walkthrough in [[2026-08-29 Obsidian community plugin submission process]] is the account of the deprecated route.

two rules bite this plugin specifically, and both are about the daemon rather than the code.

the plugin must never install or update the daemon or its dependencies. detecting one and printing an instruction is allowed, `pip install` from a plugin is a removal. that is already how it behaves, and it is now stated in the README along with the network disclosure, since undisclosed network use is the most common reason a plugin is pulled, and localhost is cheap to disclose.

the harder one: everything a plugin creates must be released on unload, and the daemon is deliberately started detached so it outlives obsidian and keeps serving the CLI and the agent sessions. either it is killed on unload, which breaks every other client, or the plugin does not own it and says so. the honest answer is the second, and it is a paragraph in the README rather than a code change, but it is the kind of thing a reviewer asks about.

three smaller ones, all handled: `isDesktopOnly` does not silence the node-module lint, so `require("http")` sits behind a `Platform.isDesktop` guard; commands carry no default hotkeys and no plugin name; settings headings are sentence case with no heading called general.

the build-step rule is the one real cost of plain javascript. the directory verifies that the shipped `main.js` matches the committed source, runs whatever npm script is named `build`, and the sample plugin's own `.gitignore` says not to commit `main.js` at all. a plugin with no bundler has nothing for that section to verify. the cheap way out is one esbuild line that bundles `src/main.js` into `main.js`, which also gets the minified build the load-time guide asks for; it is worth exactly nothing until submission, so it stays unwritten until then.
>>>>>>> 043a9802989d5522611c6a13f19ede56b31041d1

## package C, the session searcher

this is the one that pays before anyone else installs it, and the one that proves the seam. searching your own agent transcripts is a need the author has daily, the corpus is already indexed at 79,359 sections over 858 transcripts, and file provenance, which past session edited this file, is answerable from `edges` and is not answerable any other way.

it is also the cheapest proof that the scanner interface is an interface. `scan_sessions` reads Claude Code transcripts; a second scanner over `~/.gemini/antigravity-cli/history.jsonl` is a small file and a different format, and once two scanners return the same tuple the plugin story in package A is a fact rather than a claim. `~/.codex` does not exist on this machine, so codex is a third scanner written when there are transcripts to read, not a bullet in a plan.

a terminal UI is the part to leave until the search is used from a terminal often enough to be annoyed by the output format.

## how it gets distributed

the plugin and the session searcher both consume the daemon, and neither of them imports it. one speaks HTTP from javascript, the other is python that ships beside it, so the coupling between the pieces is a protocol on `127.0.0.1:44771` rather than a build. that is what decides the repository layout, and it rules out the two answers this question usually gets: a submodule contributes nothing to a plugin whose release assets are `main.js`, `manifest.json` and `styles.css`, and a cross-language build step exists only to copy files that never needed copying.

two repositories, then. `pkm-search` holds the python: the engine, the daemon and both CLIs, published to PyPI as one package with the vector half as an optional dependency group and two entry points, one for the daemon and one for the session searcher. the obsidian plugin gets its own repository because the community directory requires `manifest.json`, `package.json`, a README and a licence at the root and syncs updates from release tags, per [[2026-08-29 Obsidian community plugin submission process]], which a subdirectory of a monorepo cannot satisfy without a generated mirror repository that exists only to hold a manifest.

the session searcher is not a third repository for the same reason the obsidian features are not four plugins, worked through in [[2026-08-29 one obsidian plugin over the search daemon]]: it is the same install, the same daemon and the same scanner seam, so it is a second entry point in the same package.

the engine stays editable in this vault and CI mirrors it one way into `pkm-search`, which is what keeps the drift from coming back: one copy anyone edits, one copy anyone installs, and the second generated from the first on every push. the moment that stops being right is the first pull request from someone else, since a mirror overwrites contributions; that is when the source moves into the engine repository and the vault installs it instead of holding it.

version skew between a plugin and a daemon the user updates separately is the one thing a protocol coupling adds, and it costs an integer: `/health` reports an api number, the plugin compares it and says to upgrade rather than failing on a missing field.

what is deliberately not on this list: shipping the daemon as a bundled binary. onnxruntime plus the model is a download of a different order, obsidian reviewers are right to be wary of a plugin that fetches an executable, and the plugin already spawns a daemon it can find. `pipx install pkm-search` is the install instruction until someone reports that it is not enough.

## the sequence

<<<<<<< HEAD
second scanner first, since it is a day of work and everything else assumes it. then the session searcher, because its user exists. then the primitive split, at the point the searcher wants the extractor without ONNX, which is also when `--no-vectors` gets written and tested rather than asserted. the obsidian plugin last, because it is the most work, it is the one with a competitor, and its own prerequisite is the backlink measurement rather than any of the code above.
=======
one thing moved ahead of the scanner on 2026-08-30, and it is worth saying why rather than pretending the order held. `/graph` is engine work that the plugin needed and the scanner seam does not touch: 60 lines, cached on the index version, answered in 0.15s over 2,959 notes. it went in because the plugin is the half being used every day and the sequence below is about publishing rather than about using.

second scanner first, then, since it is a day of work and everything else assumes it. then the session searcher, because its user exists. then the primitive split, at the point the searcher wants the extractor without ONNX, which is also when `--no-vectors` gets written and tested rather than asserted. the obsidian plugin is built already but its submission is still last, because it is the one with a competitor and its prerequisite is the backlink measurement rather than any of the code above.
>>>>>>> 043a9802989d5522611c6a13f19ede56b31041d1

what would make the whole plan not worth running: nobody other than the author installing any of it. the engine is already in daily use as a skill directory, so the value of publishing is other people's bug reports and nothing else, and three packages is three READMEs, three issue trackers and three release workflows to keep for that. the version of this plan that survives a bad week is the session searcher on PyPI and the rest left as a directory in a vault.

related: [[cross-agent session indexing architecture]] for the transcript corpora, [[2026-08-27 tail reads, resuming an index at the byte it stopped at]] for how they stay cheap to reindex, [[2026-08-18 what retrieval costs as a vault grows]] for why results are locations rather than bodies, and [[2026-08-29 agentic memory - scoped devlogs vs monolithic memory]] for what the transcripts are eventually for.
