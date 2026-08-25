---
tags:
  - technical
  - git
  - search
  - ai
  - architecture
  - embeddings
---
The same index keeps getting rebuilt per domain: [[pkm metadata indexer]] for the vault, [[codegraph review|CodeGraph]] for source, a transcript adapter in [[cross-agent session indexing architecture]] for agent logs. The generalisation is a repo-level capability. Install it once into any [[git repository]] the way `git lfs install` or `git-crypt init` are installed, and that repository gains a semantic index, a rollup layer, and a set of search optimisers that travel with it. This note works out what that takes, what git hands over for free, and where it stops being worth the trouble.

This is not [[semantic search on git history]], which indexes deleted diff chunks in one vault to recover text an agent pruned. That is one query over one corpus. This is the capability underneath it, installed anywhere.

## What already exists

Three real projects and one structural ancestor, none of which is the whole idea.

`git-semantic` ([ccherrad/git-semantic](https://github.com/ccherrad/git-semantic), Rust, ~10 stars, created 2026-03-30) is the closest match. [[tree-sitter]] chunking plus embeddings, stored on a dedicated orphan branch named `semantic`. The workflow is `git-semantic index`, `git push origin semantic`, then a teammate runs `git fetch origin semantic` and `git-semantic hydrate`, which populates a local `.git/semantic.db` holding vectors and FTS5. Config sits in `.git/config`, per repo. It ships a [[GitHub actions|GitHub Actions]] recipe to re-index on push to main, which is the same move as [[repo maps via GitHub Actions]]. The pitch is the team one: one person indexes, nobody else re-embeds.

`codebase-memory-mcp` ([DeusData](https://github.com/DeusData/codebase-memory-mcp), ~40k stars) treats a committed index as an optional artifact. The file is `.codebase-memory/graph.db.zst`, a SQLite database with indexes stripped, `VACUUM INTO`-compacted and zstd-compressed at 8-13:1, so a fresh clone decompresses it and incremental indexing fills the diff. The README is explicit that it is never committed unless you want it, and tells you to gitignore the directory if you would rather everyone reindex.

`git-notes-memory` ([zircote](https://github.com/zircote/git-notes-memory), 4 stars, archived 2026-01-02) put agent memories in git notes under `refs/notes/mem`. Worth knowing because of how it failed to be git-native: the note text travelled, the sqlite-vec vectors lived in `~/.local/share/memory-plugin/` and did not.

[git-annex](https://git-annex.branchable.com/metadata/) is the oldest precedent and has nothing to do with embeddings. It stores arbitrary per-content metadata on a `git-annex` branch, keyed by content hash rather than filename, merges it in a distributed union fashion, and builds filtered view-branches from it with `git annex view`. Derived metadata on a side branch, keyed by content, syncing as ordinary refs, is exactly the architecture this note keeps arriving at.

Everyone outside that list keeps the index local and ignored:

| Tool | Index location | Committed |
| :--- | :--- | :--- |
| Zoekt | `~/.zoekt` or server shards | no, served centrally |
| Aider repomap | `.aider.tags.cache.v*/` at repo root | no, auto-gitignored |
| Continue.dev | `~/.continue/index/` (SQLite + LanceDB) | no |
| ChunkHound | `.chunkhound/` (DuckDB) | no, gitignored by design |
| CocoIndex | `.cocoindex_code/` | no, gitignored by design |
| universal-ctags | `tags` at repo root | no, it is in GitHub's official `Global/Tags.gitignore` |

[[codegraph review|CodeGraph]] belongs on that list too. Its `.codegraph/` directory is a few hundred MB and the conclusion already reached here was to put it in `~/.config/git/ignore` rather than any repo's [[gitignore|.gitignore]].

## How git-lfs and git-crypt actually hook in

Neither travels as an executable. The only thing committed is a `.gitattributes` line.

```
*.psd filter=lfs diff=lfs merge=lfs -text
secretfile filter=git-crypt diff=git-crypt
```

Everything else is written locally. `git lfs install` sets `filter.lfs.clean=git-lfs clean -- %f`, `filter.lfs.smudge`, `filter.lfs.process`, `filter.lfs.required=true`, and writes four hooks: `post-checkout`, `post-commit`, `post-merge`, `pre-push`. [[Git LFS]] feels repo-level because of three parts working together: a committed declaration file, `required=true` so a checkout fails loudly for anyone who has not installed the tool, and `post-checkout` as the after-clone bootstrap. There is no `post-clone` hook, so `post-checkout` is the standard stand-in; it fires after `git clone` with the null ref as its first argument and the flag always 1. `git-crypt` uses the same shape for [[encryption]], with the key material either in `.git/git-crypt/keys/` or GPG-encrypted in-tree.

A semantic index needs two of those three. It does not need a clean/smudge filter, because nothing has to be rewritten on the way into the object database, and a filter that fails would break checkout for a derived convenience. What it needs is the committed declaration and the hooks.

Hooks do not travel. `.git/hooks` is populated locally by `git init`, which clone runs, from the template directory, and every shipped sample is `.sample`-suffixed and inert. A repo can ship its own hooks in-tree and point at them with `core.hooksPath`, but that is a local config setting each clone opts into. There is no way to force code to run on someone else's clone, which is correct, and it means the install step is unavoidable.

The hooks that fire after content changes on disk are `post-checkout` (previous HEAD, new HEAD, flag: 1 for branch, 0 for file), `post-merge` (one arg, squash flag), `post-commit` (no args), and `post-rewrite` (`amend` or `rebase`, with old/new object pairs on stdin). There is no `post-fetch` and no `post-pull`. A `git pull` that fast-forwards fires `post-merge`; a bare `git fetch` fires nothing at all.

## Why git makes this easier than it looks

A blob's object ID is SHA-1 of `blob <size>\0<content>`, which `git hash-object` will print for any file. The filename is not part of it: names live in tree objects, and git stores no rename record whatsoever, so `git log --follow` and rename detection are diff-time heuristics over identical or similar blobs.

That single fact does most of the work.

- An embedding keyed by blob SHA is never stale. Either the key matches the content or the entry does not exist. There is no mtime to trust and no separate content hash to maintain, which is what `sections.content_sha256` is doing by hand in the [[offline GPU embeddings with incremental cache|incremental cache]].
- It survives a rename, a directory move, a branch switch, a revert and a cherry-pick with no recomputation. The vault version loses its cache when a note is renamed.
- Deduplication is free. The same vendored file across twenty branches, or across three repos on one machine, is one blob and one vector.
- History is a free time axis. `git log --format='%H %at' -- <path>` gives recency and churn per file with no extra store. `mention_heatmap.py` reconstructs this for the vault by parsing `git log -p`, because the `edges` table holds the current graph with no dates.

Three caveats that a design has to record rather than discover. Clean/smudge filters and `text`/`eol` conversion change the bytes that get hashed, so identical working-tree bytes yield different OIDs under a different `.gitattributes`. A SHA-256-format repository yields different OIDs entirely. And for an LFS-tracked path the git blob is the pointer, so the OID is the pointer's hash, not the asset's. Put the OID format and the relevant attributes in the index header so a mismatch is caught instead of silently returning wrong neighbours.

## Where the index lives

Four places, each with a real cost.

**In-tree, committed.** `.gitsemantic/index.db` arrives with every clone at no extra fetch. It also conflicts on every merge, because git cannot three-way-merge a binary SQLite file, and two people editing two different files will both rewrite it. Three answers exist and only one is honest. A custom merge driver declared as `.gitsemantic/*.db merge=gitsemantic` in `.gitattributes` can discard both sides and rebuild, which is defensible because the index is derived, but it means every merge triggers a reindex. Marking it `-merge` and taking ours is silently wrong half the time. The answer that works is to stop committing one file: shard the artifact by blob SHA prefix, one small append-only file per shard, so two branches touching different source files touch different shards and never collide, and set `union` merge on the shard files for the case where they do. That is what git-annex does and it is why it works.

**Orphan branch.** `refs/heads/semantic`, never checked out, hydrated into `.git/semantic.db`. Keeps the index out of the working tree, out of every diff, and out of `git log` on main, and it can be fetched or skipped independently, which matters on a big index. Force-push it on each index run and its history stays one commit, which is fine for a derived artifact. Costs: a second ref to keep in sync, invisible in the GitHub UI, and a cold clone has to know to fetch it.

**`git notes`.** The property that makes notes interesting is that they attach metadata to an object without changing its SHA. You can annotate a commit that is already pushed, already tagged, already signed, and history is untouched. `git notes --ref=semantic add` writes to `refs/notes/semantic`. The costs are heavy for this use. Notes are not fetched or pushed by default, needing `git push origin 'refs/notes/*:refs/notes/*'` and `git fetch origin '+refs/notes/*:refs/notes/*'`. GitHub stopped displaying them in August 2014 and never restored it, GitLab never added it. Conflicts default to a manual resolution in `.git/NOTES_MERGE_WORKTREE` unless you pass `-s union` or `-s cat_sort_uniq`. The notes tree is flat, so lookup degrades linearly as it fills. Notes are right for a small keyed payload — a caption, an 80-token summary, a model fingerprint — and wrong for 384 float32s per chunk.

**Outside the repo, keyed by blob SHA.** `~/.cache/gitsemantic/<oid[:2]>/<oid>` shared across every clone and every repo on the machine. Nothing to merge, nothing to fetch, nothing to conflict, and the cross-repo dedup comes for free. Nothing travels, so a new machine pays a full build.

The combination worth building is the fourth as the store and the first as the declaration only: one committed text file, vectors in a machine-local content-addressed cache. Add the orphan branch as an opt-in publish step for the case where a cold consumer cannot cheaply build its own.

## What travels with a clone

`.gitsemantic/config` and nothing else. It is text, so it diffs and merges like any other file, and it names everything a fetched index would have to match:

```ini
[model]
name = BAAI/bge-small-en-v1.5
dim = 384
revision = 5c38ec7
[chunker]
version = 3
policy = tree-sitter-symbol
[repo]
oid = sha1
```

The vectors, the hooks, `core.hooksPath` and the tool itself do not travel and cannot be made to.

Whether embeddings should be shared at all is a fair question. A [[vector embedding|vector]] from `bge-small-en-v1.5` is meaningless to any other model, and a mismatch does not error, it just returns bad neighbours, which is the worst failure mode available because nothing looks broken. So the hydrate step is a string comparison on `model.name`, `dim` and `chunker.version`, and a mismatch discards the fetched index and rebuilds locally rather than degrading.

Size argues the same way. 17,567 chunks in this vault is 27 MB of float32 and rebuilds in about 22 seconds on a GTX 1060 (see [[PKM indexer performance log]]); CodeGraph's index of a 618k LOC C# repo was 251 MB built in 17 seconds. Shipping 251 MB down a clone to save 17 seconds is a bad trade on any machine with a GPU. It is a good trade on a CI runner that clones cold and has none, and on a laptop that cannot run the model. That is the dividing line: share the index only when the consumer cannot cheaply build it.

## The rollup layer

[[hierarchical map-reduce note rollup]] already settled the general shape and the conclusion holds: do not materialise the tree. Build the leaf layer only, store each summary next to the hash it was generated from, and run the reduce on demand. Invalidation is one null-safe comparison, no DAG and no run manifest. A materialised rollup costs the same money as an on-demand one and pays it repeatedly for an artifact nobody read.

Two things change for a code repo, and only one of them changes the answer.

The hash gets better and free. `summary_sha` becomes the blob SHA, so a leaf summary is valid for that file content forever, in any branch, under any name, with no per-run hashing pass at all.

The grouping unit now exists, which is the part that does change. The vault rejected the recursive hierarchy because it had no level to insert: 18 notes with a `created` field, no folders, and a leaf layer that fits one 1M-token context. A repo has directories, packages and an import graph, which are deterministic groups, and a directory's tree object is already a hash over everything beneath it. A directory rollup keyed by its tree SHA is invalidated exactly when something below it changed, recursively, at zero maintenance cost. Git maintains the invalidation DAG that the vault design had to reject as too expensive to build. So the intermediate level is defensible here where it was not there.

What a repo rollup is for is narrower than it sounds. A new agent joining a repo and needing orientation before it can pick a file. A reviewer sizing a change. And a search that needs a map before it needs a page, which is Tier 1 of [[multi-repo agentic search architecture]] pushed down one level, from an org catalog of repos to a repo catalog of packages. Everything above the directory level stays generate-on-read, because a repo-wide synthesis is asked for a few times a year and by then the leaves are cached.

## Other optimisers worth folding in

Lexical FTS alongside vectors, fused with [[reciprocal rank fusion|RRF]] at k=60, same as [[vault hybrid search]]. Code makes the case stronger than prose does: an identifier like `process_payment` is the query a dense model handles worst and BM25 handles best, while "where do we handle retries" is the reverse.

A symbol graph, which is [[codegraph review|CodeGraph]]'s job and does not compete with this. It resolves symbols by structure, the index finds files by meaning, and neither does the other's work. Its measured floor is worth reusing wholesale: below roughly 15k LOC nothing was worth indexing, because a grep plus a read already answers the question.

An import graph, the repo analogue of the vault's `edges` table and [[vault graph traversal]]. One-hop expansion of a result set is cheap and reliably improves recall, whether the edges are `import` statements or wikilinks.

Recency and churn from history as a ranking signal, which nothing outside git can supply. A file touched forty times this quarter is a better answer than one untouched since 2019; a file with one author and one commit is probably vendored. The vault already runs the decay half of this at `0.5 ** (age_days / 30)` per mention day, and the same curve over commit dates per path is the code version.

Author as a scope filter. `git log --author` separates human from agent commits in a repo following the [[github co-authors for AI]] convention, which is the same trick [[semantic search on git history]] uses to isolate one reformatting wave.

## Describing non-text blobs

A repo holds bytes no text index can see: screenshots in a docs folder, a [[3D model|mesh]] in LFS, a spreadsheet, a compiled font. [[git repo is not great for binaries]] is about the storage cost of those files; this is about the fact that they are invisible to search once stored. Make them searchable by generating a text description and indexing that instead.

What generates it depends on the type, and a model is not always the answer.

For an [[image]], a local vision model — Moondream 2B, Qwen2-VL 2B, or LLaVA through Ollama — producing two or three sentences, combined with EXIF (camera, capture date, GPS), the filename and containing directory, and Tesseract OCR where the image is a screenshot. The filename and path are usually the strongest single signal and cost nothing to extract, so they go in whether or not a model runs.

For a mesh, no model at all. A stat extractor over the file gives triangle and vertex counts, bounding box, material and texture names, node and bone names, UV channel count. That is plain text and more searchable than a caption would be, because the real query is "which asset has a bone named `jaw`", not "which asset looks like a face". `trimesh` reads glTF, OBJ, STL and PLY; Assimp covers FBX. For spreadsheets and documents, extract the text and skip the description entirely.

Storage is the same content-addressed cache as the vectors, keyed by blob SHA. That buys three things at once: the description survives a rename, it never regenerates for an unchanged file, and an asset vendored into two repos is described once. A caption is also small enough to be a legitimate `git notes` payload if you want it to travel, where the vector is not.

Cost is a one-time hump. A 2B vision model on a 6 GB GPU runs roughly 1-3 seconds per image, so a thousand screenshots is under an hour once and never again for those blobs. Mesh stats are milliseconds. The recurring cost is only whatever is new.

The LFS wrinkle is worth stating plainly. With git-lfs installed, checkout runs the smudge filter and the working tree holds real bytes, so reading the file works. Two cases break that. Under `GIT_LFS_SKIP_SMUDGE=1`, common on CI and on `git lfs install --skip-smudge`, the working tree holds the pointer file instead:

```
version https://git-lfs.github.com/spec/v1
oid sha256:4d7a214614ab2935c943f9e0ff69d22eadbb8f32b1258daaa5e2ca24d17e2393
size 12345
```

An indexer that does not check will cheerfully embed that string for every asset in the repo and report success. Detect it: the file is under 1024 bytes and its first line is that version URL, or ask git with `git lfs pointer --check --file <path>`. Second, the git blob SHA of an LFS-tracked path is the hash of the pointer, not of the asset. That is still stable and rename-proof, but the better key is the pointer's own `oid sha256:` field, because it identifies the asset itself across repos. Key asset descriptions by the LFS oid, everything else by the git blob SHA, and record which one the row used. When the working tree holds only pointers, skip and record; running `git lfs pull` on a 40 GB asset repo to generate captions is not a background task.

## The case against

Most repos are too small. CodeGraph found nothing worth indexing below about 15k LOC, and that is a structural index, which pays off sooner than a semantic one does. A semantic index earns its keep when you cannot name the thing you are looking for, and in a small repo you can.

A stale index is worse than no index, because it answers confidently. Git's hooks do not cover the cases that matter: no `post-fetch`, no `post-pull`, no `post-clone`, and a bare `git fetch` fires nothing. You end up adding a file watcher, which is a daemon, which is the thing a per-repo capability was supposed to avoid.

Committing the index is a mistake in most cases, and the evidence is that every mainstream tool that could commit one chose not to. Aider auto-gitignores its cache, ChunkHound and CocoIndex gitignore theirs by design, Continue.dev keeps its index in `$HOME`, and `ctags` output is in GitHub's official ignore list. Independent teams reaching the same conclusion is a signal.

Models change every few months, and anything in history is permanent. An index committed under one model is a liability at the next swap: bytes in history nobody can regenerate the way they were made. A cache is disposable, a commit is not. The same argument applies to size, since a compressed 251 MB artifact re-committed weekly is a repo that gets slower forever.

An index is also a searchable copy of the repo. Commit it and the secret you scrubbed from a file is still sitting in an index blob in history. [[cross-agent session indexing architecture]] hit this and answered it by keeping the database beside the corpus rather than inside any repository, which is the same answer here.

The lazy alternative is the one already running on this machine. `searchd.py` holds the model resident on `127.0.0.1:44771` and serves any number of registered corpora in 13-22 ms, because the expensive part is the model and the model is corpus-independent, per [[lightning-fast unified search plugin for obsidian]]. Adding a repo is one `--vault name=/path` flag. A per-repo capability pays for the model load, the config and the freshness problem once per repo; a shared daemon pays once per machine and gets cross-corpus queries as a side effect. The only two things the daemon cannot do are exactly what the git-native version is for: produce an index that arrives with a cold clone on a machine that has never seen the repo, and produce one that survives a rename with no recomputation. If neither of those is the problem, run the daemon and skip the extension.

## Related
- [[semantic search on git history]] — the single-corpus version of this, indexing deleted diff chunks to recover pruned text
- [[codegraph review]] — the structural half of the same job, and the 15k LOC threshold below which no index pays
- [[multi-repo agentic search architecture]] — the tier above, catalog and rollup across 50-500 repos
- [[hierarchical map-reduce note rollup]] — where the rollup conclusion was reached and why the tree is not materialised
- [[vault hybrid search]] and [[agentic tooling upgrades over grep]] — the RRF pipeline and the measured case for it
- [[offline GPU embeddings with incremental cache]] — the incremental cache this replaces with a blob SHA
- [[pkm vault indexing landscape]] — the equivalent prior-art survey for Markdown vaults
- [[token efficient PKM analysis architecture]] — the retrieval and rollup economics the design borrows
- [[single-repo vs multi-repo agent search]] and [[simple options for multi-repo agent search]] — cheaper answers to the adjacent problem
- [[agent-friendly documentation tools]] — `llms.txt` and `repomix`, the no-index way to hand a repo to an [[AI agent]]
