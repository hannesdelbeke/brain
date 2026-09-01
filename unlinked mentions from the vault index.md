---
date: 2026-08-25
tags:
  - technical
  - obsidian
  - pkm
  - search
created: 2026-08-25
---
Unlinked mentions served from `.obsidian/pkm_index.db` instead of Obsidian's own pane, as `GET /unlinked` on the search daemon and `search_vault.py --unlinked` on the command line. Built on [[pkm metadata indexer]], alongside the endpoints described in [[lightning-fast unified search plugin for obsidian]].

## Why not the built-in pane

Obsidian's pane rescans the cached content of every note for the open note's title and each of its aliases, every time a note is opened. The cost is the whole vault, on every navigation, and it grows with the vault. It also has no idea what a code fence is, which is the complaint in [[Obsidian unlinked mentions include code snippets]]: a word inside a snippet is offered as a link you can never accept, because adding `[[ ]]` there breaks the code.

The index already holds every section in an FTS5 table. Asking it which sections contain a phrase is one query over 6,550 rows, and only the notes behind those rows need reading.

## How it works

1. Resolve the title to one indexed note. More than one match is an error, not a guess.
2. Read the target note's frontmatter `aliases` from the file. The index does not store aliases, so this is one file read per query. Storing them would mean a schema change and a reindex to save something that does not appear in the timing.
3. Match with an FTS5 phrase, `"covariance" OR "covar shorthand"`, over `sections_fts` with the `unicode61` tokenizer. Phrase matching is token-based, so `covariance` does not match `covariances`. The pane's substring match does, and that is a false positive you cannot act on.
4. Order the candidate sections by bm25 and take the top 200.
5. Rescan the lines of each candidate section in the file itself, which is where the line number, the exact term, and the exclusions come from.

Five things are excluded:

- The target note itself.
- Sections that already contain a `[[wikilink]]` to the target, under any alias. Those are linked mentions.
- Matches inside a fenced code block. The fence state is tracked from the first line of the file, using the same toggle [[urgent_tasks.py]] and the rest of the skill already use.
- Matches inside a `code span`. Same reason as the fence: you cannot put brackets there without changing what the code says.
- Matches sitting inside a `[[link]]` to some other note. `[[Obsidian faster startup]]` is not a mention of `Obsidian` that anyone can act on, and without this rule the results for a hub title are mostly other notes' titles.

Each hit carries the path, the section heading, the line number, and a snippet with the matched term in brackets.

## Measured

On this vault, 3,228 notes and 6,550 sections, `limit=20`, against a freshly started daemon:

| Title | Hits | Cold, first call | Warm median |
| :--- | :--- | :--- | :--- |
| `Zettelkasten` | 7 | 18ms server, 20ms over HTTP | 20ms server, 34ms over HTTP |
| `Python` | 20, capped | 47ms server, 69ms over HTTP | 41ms server, 59ms over HTTP |
| `Obsidian` | 20, capped | 42ms server, 94ms over HTTP | 48ms server, 57ms over HTTP |

Cold and warm are the same number here, unlike `/search`, which needs its embedding model resident and costs 3.0s without it. This endpoint holds no resident state: it is an FTS5 query plus a few file reads, so a daemon restart costs it nothing. The same call in a plain Python process measures 17-29ms, so most of what the daemon adds is process overhead rather than work.

Through the CLI, `search_vault.py "Zettelkasten" --unlinked` takes 0.38s against the daemon and 1.53s with `--direct`. Both are Python startup; `--direct` pays an extra second to import numpy and fastembed, which this path never uses.

A hub title costs more than a narrow one because bm25 has to rank every section containing the word before the top 200 can be taken. That is the honest ceiling of the approach and it is still tens of milliseconds.

## What was not measured

Obsidian's pane was not timed, because nothing here can time it. Doing it properly would mean running Obsidian with the developer console open, marking the backlinks view's update with `performance.mark` around `app.metadataCache` reads, or recording a CPU profile while opening a note that has many mentions and reading off the time in the backlinks worker. A number invented for the comparison would be worth nothing, so there is none. What is known without measuring is the shape: the pane's work is proportional to the vault on every note open, this endpoint's work is proportional to the number of sections containing the word.

## What is still missing

The plugin does not call this. `unified-search/main.js` only has a modal, and unlinked mentions are not a modal question, they are a question about the note you are already looking at. Wiring it up is one of two hooks:

- A right sidebar view, `registerView` plus `addCommand`, listening to `workspace.on("file-open")` and calling `GET /unlinked?note=<basename>`. This is the shape that replaces the built-in pane, and it is the larger change: a view class, a leaf, and a render loop.
- A modal mode prefix, one more entry in the plugin's `MODES` map next to `/`, `?`, `#` and `@`, taking the query as a note title. That is a handful of lines and reuses the existing suggestion rendering, but you have to type the title rather than have it follow the open note.

The prefix is the cheap one and the sidebar view is the useful one. Neither is written yet.

Other limits: one hit per section, the first one, so a section mentioning a title three times reports it once. A mention inside a URL or a markdown link label still counts as a hit. An unclosed fence marks the rest of the file as code. The results are only as fresh as the last `POST /reindex`.

## Related

- [[Obsidian unlinked mentions include code snippets]], the complaint this answers
- [[lightning-fast unified search plugin for obsidian]], the daemon and its other endpoints
- [[PKM indexer performance log]], the measurements for the rest of the index
- [[unlinked notes]], [[Obsidian Outgoing links]], [[discovery]]
