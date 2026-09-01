hybrid search (FTS5 + neural vector embeddings), link graph, and frontmatter indexer in SQLite

- [[public/pkm-search|pkm-search]] — resident search daemon and fast hybrid query engine
- [[skills/pkm-metadata-indexer/SKILL|Skill Documentation]] — commands, endpoints, and what the index holds
- [[index_pkm_meta.py]] — scan, parse, embed, and the one hybrid ranker (`search_index`)
- [[searchd.py]] — resident daemon on `127.0.0.1:44771`, one process for every vault and consumer
- [[search_vault.py]] — shell client for the daemon, searching in-process when none is running
- [[PKM indexer performance log]] — measured cost of a build and of a query
- [[lightning-fast unified search plugin for obsidian]] — the daemon and thin-plugin architecture
- [[hosted PKM vector index and note utility]]
