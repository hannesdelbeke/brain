---
date: 2026-08-24
tags:
  - technical
  - pkm
  - search
  - tools
  - review
---
What already exists for indexing a Markdown vault the way [[codegraph review|CodeGraph]] indexes a codebase, and which patterns are worth taking into the [[pkm metadata indexer]]. Star counts are from the GitHub API on 2026-08-24. For the older list of editors judged as editors rather than as corpora, see [[Obsidian alternatives]].

## Existing PKM equivalents

There is no CodeGraph for notes, but four projects overlap the stack and two hold pieces we lack.

[obra/knowledge-graph](https://github.com/obra/knowledge-graph) (106 stars, TypeScript) is the nearest in shape: SQLite with [sqlite-vec](https://github.com/asg017/sqlite-vec) and FTS5, `Xenova/all-MiniLM-L6-v2` at 384 dimensions in a 22 MB quantised model, wikilinks as edges, ten MCP tools (`kg_search`, `kg_paths`, `kg_neighbors`, `kg_subgraph`, `kg_communities`, `kg_bridges`, `kg_central`) and a Claude Code plugin.
The graph work is the real content, with Louvain community detection, betweenness centrality for bridge nodes, PageRank, BFS and all-simple-paths through [graphology](https://graphology.github.io/).
Retrieval is behind ours: no chunking at all, embedding only title plus tags plus first paragraph per file, mtime-based sync, no watcher.

[inventivepotter/dotmd](https://github.com/inventivepotter/dotmd) (45 stars, Python) is a superset on paper and runs the same `bge-small-en-v1.5` we do, stacking [LanceDB](https://github.com/lancedb/lancedb) for vectors, LadybugDB (a [Kuzu](https://github.com/kuzudb/kuzu) fork speaking Cypher) for the graph and SQLite for chunk text.
It fuses semantic, BM25 and graph with [[vault hybrid search|RRF]], then adds cross-encoder reranking, query expansion and [GLiNER](https://github.com/urchade/GLiNER) zero-shot entity extraction over structural edges (HAS_SECTION, LINKS_TO, HAS_TAG, MENTIONS, CO_OCCURS).
Two traps rule it out for a live vault: reindexing is full rather than incremental, and the MCP server cannot run at the same time as the REST API because the graph database holds a single connection.

[memtomem](https://github.com/memtomem/memtomem) (13 stars, Python, Apache-2.0) is our architecture built independently, with heading-aware chunking, BM25 plus dense plus RRF, ONNX `bge-small-en-v1.5`, and chunk-level SHA-256 diffing so only changed chunks re-embed.
It already ships the code-fence idea, with tree-sitter for JavaScript and TypeScript, AST for Python and structure-aware parsing for JSON, YAML and TOML, and its `mem_do` meta-tool routes non-core actions through one entry point for the same reason `codegraph_explore` exists.

[ehc-io/qmd](https://github.com/ehc-io/qmd) (16 stars, TypeScript, MIT) has the best chunker of the group: chunks target 900 tokens with 15% overlap, but the break point is chosen by scoring Markdown elements (H1 100, H2 90, code block 80, blank line 20) inside a 200-token window with distance decay, so code fences survive intact.
Fusion is RRF at k=60 with the original query weighted twice and a small top-rank bonus, then qwen3-reranker-0.6b blends by position, 75/25 retrieval to reranker at ranks 1-3 and 40/60 at rank 11 and below.
Everything runs on [node-llama-cpp](https://github.com/withcatai/node-llama-cpp) with about 2 GB of GGUF models, updates are manual.

Seen and not worth adopting: [smart-connections-mcp](https://github.com/msdanyg/smart-connections-mcp) only reuses vectors the Smart Connections plugin already wrote, [MegaMem](https://github.com/C-Bjorn/MegaMem) wraps [Graphiti](https://github.com/getzep/graphiti) temporal graphs but sits in public beta, and [drewburchfield/obsidian-graph](https://github.com/drewburchfield/obsidian-graph) fails the local requirement by calling the Voyage AI API.

## Vault systems judged as corpora

[AFFiNE](https://github.com/toeverything/AFFiNE) leads on stars at 71.8k and is the least relevant, because a canvas has no clean text projection for an indexer to read.
[memos](https://github.com/usememos/memos) at 62.5k is a lightweight capture stream with REST and gRPC APIs, easy to index but too flat to hold a link graph worth traversing.
[joplin](https://github.com/laurent22/joplin) at 56.1k has the best portability story but keeps notes in its own SQLite store rather than a folder an external indexer can watch.

[siyuan](https://github.com/siyuan-note/siyuan) at 46.0k is the most interesting failure.
Its block database is genuinely queryable, with SQL embedded in documents, a `siyuan sql` and `siyuan search` CLI that emits JSON without a running server, an HTTP kernel plus WebSocket API, and search that reaches inside PDF, Word, Excel and txt assets with Tesseract OCR behind it.
Blocks are exactly the granularity a retrieval layer wants, one level below the note.
The cost is the on-disk format: documents are `.sy` JSON, references use a `siyuan://` protocol, third-party sync corrupts the workspace, and the Docker build cannot import Markdown at all.

[logseq](https://github.com/logseq/logseq) at 44.6k is mid-rewrite, which decides it.
The file build stores Markdown or Org files queried through [datascript](https://github.com/tonsky/datascript) Datalog held in memory, while the DB version moves storage into SQLite and sits in beta with a readme warning that data loss is possible, alongside an alpha mobile app and alpha realtime sync.

[TriliumNext/Trilium](https://github.com/TriliumNext/Trilium) at 37.6k stores everything in SQLite as a deep tree with note cloning, and its distinguishing feature is that notes contain runnable JavaScript that queries other notes, making it a scripting host rather than a corpus.
[khoj](https://github.com/khoj-ai/khoj) at 36.7k is the only entry that is an AI layer rather than an editor, with semantic search over Markdown, PDF, Org, Word and Notion, agents with custom knowledge and persona, and Docker self-hosting.
It is the closest finished product for this job, and the reason to keep building is that it owns model, agent and retrieval together where ours is retrieval only, handing ranked `path:line` targets to whichever agent is already in the session.

[silverbullet](https://github.com/silverbulletmd/silverbullet) at 5.9k is the smallest and best architected for scripting, with Markdown pages in a Space, a Rust server exposing an HTTP file API and an `sb` CLI, and objects extracted from Markdown and queried through SLIQ, its own query language.
[anytype](https://github.com/anyproto/anytype-ts) at 8.7k stores typed objects rather than Markdown and syncs peer to peer, ruling out folder watching.
[quartz](https://github.com/jackyzha0/quartz) at 13.1k and [Foam](https://github.com/foambubble/foam) at 17.4k are not vault apps but vault layers, a static publisher and a VS Code extension, and both read a plain folder of Markdown, which is the property that makes a vault indexable at all.

## Patterns worth stealing

[silverbullet](https://github.com/silverbulletmd/silverbullet) has the best idea here: index-time object extraction. Tasks, tags, headers and frontmatter fields become typed objects at index time, so the query surface is a schema rather than a blob. That is the vault version of CodeGraph's synthetic route nodes, and it turns "unfinished tasks tagged gamedev since June" from a semantic guess into a deterministic filter.

[siyuan](https://github.com/siyuan-note/siyuan) contributes stable block ids that survive edits above and below them, where a `path:line` target goes stale the moment a paragraph is inserted, and OCR over attachments, which is real text the vault holds and we index none of.

[joplin](https://joplinapp.org/help/apps/search/) is the cheapest steal: BM25 through an external-content FTS5 table with per-column weights, the standard shape being `bm25(notes_fts, 10.0, 1.0)` to weigh a title match ten times a body match. Column weights are one argument on a query we already run, and `content=` keeps the index without storing the text twice.

[quartz](https://quartz.jzhao.xyz/features/full-text-search) strips Markdown before indexing, keeps separate title, content and tag indexes with title weighted above content, tokenises CJK, and returns the most relevant 30 words rather than the whole match. The excerpt is the part to copy, since a ranked list of 30-word windows costs a fraction of the same list of full chunks.

[Foam](https://github.com/foambubble/foam) models placeholders (links pointing at notes that do not exist) and orphans (notes with no link either way) as first-class objects with their own panels. Placeholders are not errors in this vault, they are the convention, so indexing them as nodes turns the convention into a queryable backlog. Foam also reports ambiguous wikilinks as diagnostics and resolves same-name notes by minimum unique identifier, which beats resolving to the first match with a warning.

[Trilium](https://docs.triliumnotes.org/user-guide/advanced-usage/attributes/attribute-inheritance) has the most transferable metadata model, with inheritable attributes applying to a note and every descendant, `template` relations inheriting attributes without a parent-child link, and relation definitions carrying an inverse the app maintains on the target automatically. The folder analogue is a defaults file per directory, and its `archived` label, which hides a subtree from search, is the exclusion mechanism the indexer lacks.

[logseq](https://github.com/logseq/logseq) queries an in-memory graph with Datalog, the same lesson as SLIQ from the other end: a structured query language composed with ranked results, not instead of them.
[khoj](https://github.com/khoj-ai/khoj) scopes an agent to a subset of the corpus, which is a path filter on a query we already run and cuts both noise and how much private material reaches a model.
[dotmd](https://github.com/inventivepotter/dotmd) derives `CO_OCCURS` edges between notes mentioning the same entity without either linking the other, the one signal wikilinks structurally cannot carry, and also the expensive one, so it belongs behind a flag.
[qmd](https://github.com/ehc-io/qmd) keeps models resident in VRAM behind an HTTP daemon on port 8181, which is the same conclusion the [[lightning-fast unified search plugin for obsidian|search daemon]] reaches from first principles.
[memtomem](https://github.com/memtomem/memtomem) splits install into tiers so BM25 alone is 40 MB against 250 MB for the full stack, worth copying for anything another machine has to run.
[memos](https://github.com/usememos/memos) is a reminder that heading chunking with overlap makes short notes worse by splitting them into near-duplicate fragments, so a length threshold below which a note is one chunk costs a conditional.
[anytype](https://github.com/anyproto/anytype-ts) types every object, and the honest version for a Markdown vault is a frontmatter type registry checked at index time, so a note claiming a type without the fields it implies gets reported rather than silently indexed.

## Verdict

Keep the indexer. It wins on the two axes that decide daily use, GPU incremental reindexing and hybrid recall, and dotMD losing incremental indexing alone disqualifies the closest feature match.
The survey pushes the same way: every system that adds structure worth having (SiYuan blocks, Trilium trees, Anytype objects) pays for it by leaving plain Markdown, and plain Markdown in a folder is what lets the indexer, Quartz, Foam, Obsidian and git all read the same bytes.

Ordered by payoff per line of code, the first four are an afternoon and the rest are projects.
Joplin's per-column BM25 weights, an argument on a query we already run.
Quartz's 30-word excerpt in place of returning whole chunks.
A length threshold below which a short note indexes as one chunk.
Foam's placeholders as index nodes, making the unwritten-`[[link]]` convention a queryable backlog.
Then qmd's break-point scorer to replace plain `##` splitting, cheaper than tree-sitter and it fixes split code fences directly, with tree-sitter kept only for tokenising fence contents into FTS5.
Then a rerank stage over the top 30 RRF candidates with position-aware blending, behind the daemon so it does not pay a cold start per call.
Then graph algorithms from obra/knowledge-graph, since PageRank, Louvain communities and bridge nodes run on the edge list [[vault graph traversal|already parsed]] and graphology is one dependency.
Silverbullet's typed objects are the largest and the one that changes the query surface rather than the ranking, so it wants its own note before any code.

Nobody in either list ships CodeGraph's watcher, debounce and staleness banner for Markdown, which stays the smallest available win.
