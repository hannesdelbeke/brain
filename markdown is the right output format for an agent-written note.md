---
aliases:
- note format for agents
- markdown vs json vs sql for notes
tags:
- technical
- pkm
- research
---

a note an agent writes should be a markdown file with wikilinks, not a database row, not JSON, and not a stored embedding. markdown is the cheapest container measured, the only one all four readers handle — human, agent, search index, git — and the only one where the file's own boundaries do the work a schema would otherwise have to. what belongs in another format is the data a note *cites*, not the note.

## token cost of the container

150 random notes from [brain](https://github.com/hannesdelbeke/brain), same content, four serializations, cl100k tokenizer, measured 2026-09-02:

| format | tokens | vs markdown |
|:---|---:|---:|
| markdown | 78,926 | — |
| xml | 82,160 | +4.1% |
| sql insert | 82,225 | +4.2% |
| json | 91,750 | +16.2% |

JSON is worst because prose is full of newlines and quotes and every one of them gets escaped. markdown wins because it has almost no container at all: the markup is the content. for scale, the `[[ ]]` markup argued about in [[2026-09-02 what wikilink markup costs a machine reader]] is 2.56% of the vault, so the container choice is a bigger lever than the link syntax inside it.

## why prose does not want to be a database

a note is claims in sentences. moving it into SQL turns the argument into a `TEXT` blob in a row and hands you a schema to maintain, in exchange for query power that does not apply to sentences. what it costs:

- **line diffs**, and with them git as the memory layer — a blob column has no `git log -p`
- **partial reads** — an agent reads `start_line` to `end_line` off the index today, where a blob is all or nothing
- **escaping safety** — string literals are where content gets silently corrupted, and this vault has already lost characters that way once
- **the human** — Obsidian is the interface where the person who decides what a note means actually edits it

format sensitivity also shrinks as models get larger. the Microsoft/MIT format study ([arXiv:2411.10541](https://arxiv.org/html/2411.10541v1), He et al. 2024) measured up to 40% swing by format on GPT-3.5-turbo, much less on GPT-4-class, with markdown the stronger template for the larger model. there is no comprehension win waiting in JSON.

## storing raw vectors instead is the same idea, one step worse

a vector is not a store of meaning, it is a lossy fingerprint of it. `bge-small-en-v1.5` gives 384 float32 dimensions, **1,536 bytes per chunk**, and the numbers below are from this vault's own live index:

| | source text | stored vectors |
|:---|---:|---:|
| private vault, 973 notes / 9,231 chunks | 4.0 MB | 14.2 MB |
| brain, 3,195 notes | 4.6 MB | 46.8 MB index total |

**the vectors are 3.5x the size of the words they encode**, so there is no compression argument. the disqualifying problems are the other three:

- **not invertible in practice.** you cannot reconstruct a note from its embedding. research inverting embeddings back to text ([Morris et al. 2023](https://arxiv.org/abs/2310.06816)) recovers a surprising amount, enough to matter for [[2026-08-30 sharing a vector index across people and orgs]], but it is approximate reconstruction, not storage.
- **model lock-in.** swap the embedding model and every vector is scrap. the only way to rebuild is to re-embed the text, which means the text has to still exist, which means the vector was always a cache.
- **no reader can read it.** a language model consumes tokens through a text interface; it cannot be handed 384 floats as context. a human cannot read them, grep cannot search them, and a diff of two vectors says nothing about what changed.

that makes an embedding a derived artifact by definition — correctly gitignored, correctly rebuilt by [[pkm metadata indexer]], and correctly absent from the note itself. the general rule it belongs to: **never store what a parser can derive from the source.**

## if you want to store meaning compactly, store short text

the compressible thing is not the encoding, it is the wording. a summary line, a claim as a filename, an assertion-style heading — all of them survive a model swap, stay greppable, and stay editable by the person who disagrees with them. [[header extraction for token-efficient retrieval]] measured the heading version of this at 77.5% fewer tokens per note scanned, with assertion-style headings reaching full zero-read capability where generic labels like "Overview" force opening the file anyway. that is meaning stored as meaning, in the only format both readers share.

## where another format does win

- **tabular data is not a note.** a benchmark table, a metrics log, a day-by-day record — rows belong in a CSV or JSONL file the note links to. you get diffs that name the row that changed, re-analysis without reparsing prose, and no token cost for the rows nobody asked about. it also makes a table impossible to drift from the run that produced it.
- **machine-to-machine payloads** are JSON. a subagent's structured result or a schema-enforced tool output is transport, not a note, and the escaping overhead buys parse safety there.
- **derived indexes** are SQLite with vectors inside, which is what already runs here — markdown as source of truth, index rebuilt from it, never the other way round.

## related notes
- [[2026-09-02 what wikilink markup costs a machine reader]] — what the link markup inside the file costs
- [[path alias is human facing not agent]] — how to write the links themselves
- [[model weights vs vector embeddings vs map-reduce]] — the three places knowledge can live, and what each costs
- [[header extraction for token-efficient retrieval]] — storing meaning as shorter text, measured
- [[pkm metadata indexer]] — the derived index this note argues should stay derived
- [[vector embedding]] — what the numbers in a vector actually are
