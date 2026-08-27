---
date: 2026-08-27
tags:
  - technical
  - search
  - pkm
  - research
---
Written after a survey, because the engine in [[pkm-search]] was starting to feel like something nobody else had built, and that feeling is usually wrong. It was wrong. Eight searches across the plugin ecosystem, local search engines with no Obsidian in them, embeddable retrieval libraries, agent-transcript tools, log shippers and the retrieval literature. What follows is what exists, what it does better, and the two things left that nothing found does.

## The vault half is a crowded, solved problem

[Obsidian Hybrid Search](https://forum.obsidian.md/t/hybrid-search-hybrid-search-mcp-server-cli-for-ai-assistants-bm25-semantic-obsidian-native/112491), posted March 2026, is the same design down to the storage layer: SQLite FTS5 for BM25, local embeddings, fuzzy title matching, all three fused with reciprocal rank fusion into a single SQLite file at the vault root, served to an assistant over MCP, with a file watcher doing incremental indexing. It bundles `multilingual-e5-small` and adds an optional cross-encoder rerank, neither of which we have. It is ahead of us on the watcher, which is our next open item.

Others in the same shape:

| Tool | Lexical | Vector | Fusion | Notes |
| --- | --- | --- | --- | --- |
| [Obsidian Hybrid Search](https://forum.obsidian.md/t/hybrid-search-hybrid-search-mcp-server-cli-for-ai-assistants-bm25-semantic-obsidian-native/112491) | FTS5 | e5-small, local | RRF plus cross-encoder | MCP server, chokidar watcher |
| [VaultSearch](https://community.obsidian.md/plugins/vault-search) | FTS5 through sql.js | transformers.js, on-device | RRF | desktop only, plugin |
| [obsidian-qmd](https://github.com/thirteen37/obsidian-qmd) | MiniSearch | MiniLM-L6, hnswlib | RRF at k=60 | heading hierarchy, query expansion |
| [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) | none | transformers.js | none | vector only, heading-aware chunks |
| [Omnisearch](https://github.com/scambier/obsidian-omnisearch) | MiniSearch BM25 | none | none | lexical only |
| [khoj](https://github.com/khoj-ai/khoj) | yes | local through Ollama | bi-encoder plus cross-encoder | self-hosted daemon |
| [Reor](https://github.com/reorproject/reor) | none | transformers.js into LanceDB | none | standalone app |

Reciprocal rank fusion over BM25 and vectors is textbook rather than clever: [Vespa](https://docs.vespa.ai/en/learn/tutorials/hybrid-search.html), [Meilisearch](https://www.meilisearch.com/blog/hybrid-search) and [Typesense](https://typesense.org/docs/30.2/api/vector-search.html) all ship it as a documented feature. The embedded-vector layer has a dozen options: [sqlite-vec](https://github.com/asg017/sqlite-vec), [LanceDB](https://github.com/lancedb/lancedb), [DuckDB VSS](https://duckdb.org/docs/lts/core_extensions/vss), [usearch](https://www.unum.cloud/usearch). Brute-force NumPy under 300,000 sections remains a defensible choice, but it is a choice among many rather than an absence of options.

## Outside the plugin ecosystem

The plugins are one shelf. A second survey looked at local search engines with no Obsidian in them, and the same architecture is there too.

| Tool | Lexical | Vector | Fusion | Shape |
| --- | --- | --- | --- | --- |
| [txtai](https://github.com/neuml/txtai) | BM25 sparse index | local Hugging Face models | sparse and dense indexes in one embeddings database | Python library, in process, FastAPI and MCP servers optional |
| [SeekStorm](https://github.com/SeekStorm/SeekStorm) | BM25F | ANN, Model2Vec embeddings | reciprocal rank fusion, built in | Rust, library or REST server, incremental indexing |
| [khoj](https://github.com/khoj-ai/khoj) | no | local sentence-transformers through ONNX | none, vector only | self-hosted daemon, needs Postgres and pgvector |
| [Typesense](https://github.com/typesense/typesense) | yes | built-in S-BERT and E5 | weighted, an `alpha` between the two | single binary server |
| [Meilisearch](https://github.com/meilisearch/meilisearch) | yes | yes | documented as hybrid, fusion method not stated | server, MCP server exists |
| [Recoll](https://www.recoll.org) | Xapian | no | none | desktop index with a real-time file monitor |
| [RAGFlow](https://github.com/infiniflow/ragflow) | full text | external embedding services since the slim build | fused re-ranking | Docker platform on Elasticsearch |
| [privateGPT](https://github.com/zylon-ai/private-gpt) | no | local through Ollama | none | RAG API, Chroma store |

The closest of these to what we built are txtai and SeekStorm. Both are libraries rather than applications, both do the whole lexical-plus-vector-plus-fusion stack locally, and neither knows anything about markdown structure, heading-level chunking, a link graph, or a location payload of `(path, line, heading)`.

## The transcript half has fewer players

[claude-history](https://github.com/raine/claude-history) is the closest thing to the transcript half of this engine: MIT, a terminal interface over Claude Code JSONL, and its search is hybrid rather than fuzzy, embedding conversation chunks locally with a downloaded model and fusing that conversation-level ranking with lexical evidence. It indexes tool results, thinking and subagent content, and it embeds a compact routing passage per conversation rather than every chunk, which is the opposite trade from section-level vectors: cheaper to build, coarser to point at.

[SpecStory](https://github.com/specstoryai/getspecstory) indexes agent sessions from ten or more coding tools into `.specstory/history/` and searches them full text, local first with optional cloud sync. [claude-history-explorer](https://github.com/adewale/claude-history-explorer) does regex over the same JSONL. [claude-code-log](https://github.com/daaain/claude-code-log) renders transcripts to HTML and does not search them. [Cursor History](https://github.com/S2thend/cursor-history) does keyword search over Cursor's chat SQLite. Chat interfaces have their own: [Open WebUI](https://docs.openwebui.com/features/chat-conversations/chat-features/history-search/) searches its SQLite lexically, and [LibreChat](https://www.librechat.ai/docs/configuration/meilisearch) bolts on Meilisearch. Further out, [Atuin](https://github.com/atuinsh/atuin) does this for shell history and [OpenRecall](https://github.com/openrecall/openrecall) does it for screenshots by OCR.

Neither survey found a tool that indexes a personal notes corpus and agent transcripts in one ranked index, which is the claim this engine rests on.

The agent-memory systems are a different animal wearing similar clothes. [Zep](https://www.getzep.com/) builds a temporal knowledge graph with invalidation, [mem0](https://mem0.ai/) does multi-signal retrieval over extracted memories, [Letta](https://github.com/letta-ai/letta) tiers core against archival memory, [Cognee](https://www.cognee.ai/) builds a graph through an extract-cognify-load pipeline. All of them index what a model decided to remember. None index the transcript as a document you can search.

## What you would install instead of writing the retrieval math

The retrieval math here is an FTS5 query, a dot product over a float32 matrix and a reciprocal rank fusion, about 300 lines. What replaces exactly that, in process, offline:

- [txtai](https://github.com/neuml/txtai) replaces all three in one install, at the cost of its own storage and its own document model.
- [LanceDB](https://github.com/lancedb/lancedb) has full text, vectors and a reranker API in an embedded columnar store.
- [Infinity](https://github.com/infiniflow/infinity) has an embedded Python mode with dense and sparse vectors, full text, and a choice of reciprocal rank fusion, weighted sum or ColBERT reranking.
- [sqlite-vec](https://github.com/asg017/sqlite-vec) is vectors only, in SQLite, meant to be paired with FTS5 and fused by hand. [vectorlite](https://github.com/1yefuwang1/vectorlite) is the approximate version of the same idea on hnswlib. [sqlite-vss](https://github.com/asg017/sqlite-vss) is its retired predecessor.
- [bm25s](https://github.com/xhluca/bm25s) plus [FAISS](https://github.com/facebookresearch/faiss) plus [ranx](https://github.com/AmenRa/ranx) is the minimal trio if the parts stay separate; ranx alone is twenty-five fusion algorithms including reciprocal rank fusion, and [rerankers](https://github.com/AnswerDotAI/rerankers) is the same idea for the cross-encoder layer.
- [DuckDB](https://duckdb.org/docs/current/core_extensions/full_text_search) with its full text and vector extensions is the embedded database that gets closest to SQLite plus FTS5 plus vectors without leaving SQL.

What every one of them costs is the same thing: storage stops being one SQLite file the rest of the tool already reads, and chunk boundaries stop being ours. That is the whole reason the accounting in [[2026-08-27 build or install, measuring the engine against the plugin that already exists]] comes out where it does.

## Usage-based edges are old research and no shipped product

The plan in [[2026-08-27 every read is a write - co-retrieval as synapse strength]] has deep literature behind it and, as far as the survey found, no shipped implementation in a notes tool. [Amazon's item-to-item collaborative filtering](https://www.cs.umd.edu/~samir/498/Amazon-Recommendations.pdf) is the co-visitation matrix in its canonical form. [Radlinski and Joachims on query chains](https://www.cs.cornell.edu/people/tj/publications/radlinski_joachims_05a.pdf) extract preferences from searches in one session, and [unbiased learning to rank](https://www.cs.cornell.edu/people/tj/publications/joachims_etal_17a.pdf) gives inverse propensity scoring for the position bias that will otherwise poison the signal. [Anderson's spreading activation](https://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/66SATh.JRA.JVL.1983.pdf) and ACT-R argue for decay by path distance rather than flat co-occurrence counts, and the whole idea is [Bush's memex trails](https://www.w3.org/History/1945/vbush/vbush7.shtml) from 1945.

The PKM tools that suggest links — DEVONthink's See Also, Smart Connections, TheBrain — weight by content similarity. None weight by what was retrieved together. The four failure modes the literature names are the design brief: popularity bias, position bias, self-reinforcing feedback loops, and cold start on a new note.

## Tail reads are a twenty year old wheel

Every log shipper solved [[2026-08-27 tail reads, resuming an index at the byte it stopped at]] before we did, and Splunk solved it in the same shape. Its fishbucket stores a CRC of the first 256 bytes as file identity, a `seekAddress` byte offset, and a `seekCRC` of the content at that offset; a mismatch or a file too short to validate means rewrite, read in full. Substitute a hash of the 4 KB before the offset for the seek CRC and that is our design.

[Filebeat](https://www.elastic.co/docs/reference/beats/filebeat/filebeat-input-filestream) offers fingerprint, native inode plus device, or path as the file identity, and defaults to a CRC over the first 1024 bytes because inodes get reused. [Logstash](https://www.elastic.co/guide/en/logstash/8.19/plugins-inputs-file.html) stores inode, device major and minor, offset and timestamp, and expires entries after N days to survive inode recycling. [Fluentd](https://docs.fluentd.org/input/tail) keeps a position file of filename, offset and inode, with a `rotate_wait` grace period holding the old handle open. [Vector](https://vector.dev/docs/reference/configuration/sources/file/) fingerprints by CRC over the first lines. [journald](https://www.freedesktop.org/software/systemd/man/latest/sd_journal_get_cursor.html) hands out an opaque cursor per entry instead.

What they all have and we do not is file identity independent of the path, which is what makes rotation survivable. It does not apply here: a transcript is named by a session uuid, is never rotated and is never rewritten, so a path is a stable identity, and a renamed file is a new path that gets read in full while the old path's rows are deleted. That costs a reparse and loses nothing. The one idea worth taking if the corpus ever changes shape is Filebeat's head fingerprint, which recognises a moved file rather than reparsing it.

Three of the criticisms that survey turned up do not apply, and the reasons are worth writing down so they are not rechecked later. A rewrite by atomic rename is caught by the prefix hash. A UTF-8 multibyte character cannot be split by a checkpoint, because checkpoints only happen at a newline and UTF-8 is self-synchronising. Coarse mtime granularity cannot hide an append, because an append always changes the size, and a size larger than the recorded one already forces a read.

## What is left that is ours

Two things, after all of that.

The corpora share one index. A transcript and a note are the same kind of row, ranked by the same query, so a search crosses from what was written to what was done without a second system. The tools above index a vault or index sessions; none do both through one ranker.

Every file a tool touched is an edge in the same graph as the wikilinks. That makes "which session last edited this file" a graph query rather than a git blame, and nothing in the survey does it.

Neither is a large invention. Both are consequences of the `collect=` seam, which is the actual idea worth having: the index is source-agnostic after the scan, so a corpus is a scanner rather than a system.

## What to steal

- A cross-encoder rerank on the top of the fused list, which Obsidian Hybrid Search and khoj both have and which is the standard next accuracy step.
- Inverse propensity scoring before co-retrieval edges are trusted, because the ranker's own ordering will otherwise be measured as relevance.
- Decay by path distance from the spreading activation model, rather than counting co-occurrences flat.
- Filebeat's head fingerprint as file identity, if the transcript corpus ever gains rotation.

Whether to stop building and install one of these instead was then measured on the same vault: [[2026-08-27 build or install, measuring the engine against the plugin that already exists]].
