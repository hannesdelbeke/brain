---
tags:
- technical
- pkm
- research
- obsidian
---

> [!summary] eli5
> wikilinks do not measurably confuse a machine reader — the `[[ ]]` brackets move a chunk's embedding by about 1% against a 44-point gap to unrelated text, and they cost 0.7-2.6% of a vault's tokens. the real cost is elsewhere: 17-18% of wikilinks in these two vaults point at a note that does not exist, and a link an agent has not opened looks exactly like one it has. the reading-comprehension half is measured only for retrieval, not for question answering — that probe is written up below but unrun, no reader model was available. a section below compares Obsidian's two alias features: frontmatter aliases help a machine reader, display aliases inside a link hide on average 60% of the target name's length from it.

> do wikilinks make agents understand text worse?

## the numbers

measured with [[wikilink_cost_experiment.py]] over two real vaults on 2026-09-02, [brain](https://github.com/hannesdelbeke/brain) (3,195 notes, short concept notes, dense linking) and a second private vault (973 notes, long prose research notes).

| measurement | brain | private vault |
|:---|:---|:---|
| tokens added by `[[ ]]` markup | 2.56% (28,500 of 1.11M) | 0.74% (7,456 of 1.00M) |
| per-note median / p95 | 3.55% / 28.57% | — |
| links pointing at no note | 18.0% (1,932 of 10,719) | 17.0% (2,512 of 14,769) |
| links sitting mid-phrase | 51.6% | 73.4% |
| link forms | 8,996 name-only, 1,309 alias, 425 path-alias | 3,649 / 180 / 39 |

embedding shift, 200 random linked paragraphs from brain through `BAAI/bge-small-en-v1.5`: **cosine 0.9884 mean** between a paragraph and the same paragraph with links stripped, worst case 0.8945. the same sample's unrelated paragraphs sit at 0.5579 cosine from each other, so the markup moves a chunk roughly 1% in a space where the gap to a genuinely different chunk is 44 points. it is noise, not signal.

## so the parsing worry is the wrong worry

both the vector and the lexical path handle brackets fine, confirming the earlier bench in [[semantic search]] where `unloading [[dishwasher]]` scored 0.944 against the query `unload dishwasher`. subword tokenizers split `[` and `]` into punctuation tokens with almost no semantic weight, and FTS5 treats them as word boundaries. nothing here suggests a model reads a linked sentence worse than a plain one.

**what does break is literal substring search.** over half the links in brain and nearly three quarters in the private vault sit directly against a word — `unloading [[dishwasher]]` does not contain the string "unloading dishwasher", so an agent that greps for the phrase misses a note that plainly says it. that is a real capability loss for the cheapest tool an agent has, and it is the strongest argument for keeping [[pkm metadata indexer]]'s hybrid index in front of grep rather than expecting grep to work on a linked vault.

## the actual hazard: a link is an unread reference

**about one wikilink in six points at nothing.** 18.0% in brain, 17.0% in the private vault. some are deliberate forward links to notes not yet written, which is a normal Obsidian habit, but nothing in the text distinguishes those from a typo or a renamed note. a broken link and a link to a 3,000-word note look identical to a reader that has not opened either.

that is where an agent goes wrong, and it is a behaviour problem rather than a parsing one: `[[hierarchical map-reduce note rollup]]` reads as a citation, and an agent under time pressure can treat it as evidence for a claim without opening it. the risk compounds because the link text is usually a confident-sounding assertion — the vault's own filename convention makes it one deliberately. the same failure shape produced a wrongly-labelled "fabricated" benchmark table in this vault in august, where a claim about content nobody had opened got stated as fact.

## the pointless cost: path-alias links

425 links in brain and 39 in the private vault use the `[[dir/note name|note name]]` form, which pays for the name twice plus a path the reader does not need, for zero benefit over `[[note name]]`. Obsidian resolves name-only links regardless of folder, which is why name-only is the written convention in both vaults. these are cheap to fix and the fix also survives a note being moved.

## aliases are two different features wearing one name

[[Obsidian aliases]] covers both, and for a machine reader they pull in opposite directions.

**frontmatter aliases help.** 1,393 of them across 753 notes in brain. they are written once per note, cost nothing per mention, and add surface forms a search can hit — `RAG` finds [[retrieval augmented generation]] because the alias is there. more of these is strictly better for retrieval.

**display aliases inside a link cost.** `[[target|display]]` pays for both names and then shows the reader only the short one. 1,735 of these in brain, and the breakdown is unflattering:

| form | count | what it does |
|:---|---:|:---|
| display identical to target | 227 | pays twice for the same string, zero benefit |
| case or punctuation variant | 30 | near-zero benefit |
| display shorter than target | 1,018 | hides information the writer already wrote |
| display longer than target | 429 | adds information, the useful direction |
| unrelated wording | 31 | reader cannot tell what is behind it |

the shortening links keep **40% of the target name's length on average**, median 36%. so roughly 60% of what the filename says is present in the file and absent from the sentence a reader actually reads. in a vault where filenames are written as assertions, that discarded 60% is the claim itself: `[[extra long note names can contain more information]]` tells an agent what is behind the link, and `[[extra long note names can contain more information|my note]]` tells it nothing while costing more tokens than either name alone.

### the rename argument, and why it inverts

the honest case for the aliased form is stability: Obsidian rewrites `[[old name]]` into `[[new name]]` on rename, editing your sentence under you, while `[[old name|my note]]` keeps the prose fixed and lets only the target move. the display word is locked in time.

for an assertion-named vault that protection points the wrong way. if the filename is a claim, renaming it is revising the claim, and a sentence that still displays the old wording is now quietly asserting something the vault no longer believes — with no broken link and no diff to notice it by. the rewrite Obsidian performs is the feature: it surfaces every place the old claim was relied on. locking the display text buys prose stability by paying in stale claims, which is the more expensive of the two.

### what an AI writing notes should do instead

- **default to the bare full name.** `[[extra long note names can contain more information]]`, no pipe. cheapest of the three forms and the only one that carries the claim to a reader that has not opened the target.
- **write the sentence around the link,** not the link into the sentence. the subject-first convention already asks for this, and a name that is a full noun phrase usually drops into a sentence unchanged once the sentence is built for it.
- **keep grammar outside the brackets.** `[[header extraction for token-efficient retrieval]] measured 77.5%` rather than an alias that bends the name into the clause.
- **put alternate names in frontmatter, once,** instead of in every link. short forms, acronyms and older titles belong there, where they serve search and cost nothing per mention.
- **if display text must differ, make it longer than the target, not shorter.** the 429 expanding links are the only alias category that leaves a machine reader better off.

that leaves one legitimate use: a target whose name is a formal identity the sentence cannot use as a common noun, a person or a product. even there, restructuring the sentence usually beats the pipe.

**one mechanical cleanup is available now:** the 227 identical and 30 case-variant aliases can be rewritten to bare links with no loss of meaning to either reader, and the 425 path-alias links from the section above collapse the same way.

## what this does not measure

question-answering accuracy. the probe worth running: take real paragraphs, ask factual questions answerable from the paragraph itself, and compare accuracy between the linked and stripped versions across a couple of small models. then run a second condition where the answer lives only behind a wikilink whose target is not supplied, where the correct answer is "not in this text" — that measures the fabrication rate the section above argues is the real risk. both were designed for this note and neither ran: no API key was configured, the [[antigravity]] cli pool had hit its daily quota, and no local model runtime is installed on this machine.

the prediction, recorded before running so it can be wrong later: no significant accuracy difference on the first condition, and a measurable fabrication difference on the second.

## reproducing

```
python skills/pkm-metadata-indexer/wikilink_cost_experiment.py <vault> [--sample 200] [--no-embed]
python skills/pkm-metadata-indexer/wikilink_cost_experiment.py --demo
```

the embedding pass needs `fastembed`, everything else is stdlib plus `tiktoken`.

## related notes
- [[Obsidian aliases]] — the alias feature itself, both forms
- [[semantic search]] — the earlier bench showing brackets barely move retrieval scores
- [[wikilink]] — what the link form is and what it does in a graph
- [[are wikilinks legacy with embedded vector]] — whether hand-made links still earn their keep next to vector search
- [[2026-08-27 synapse links vs wikilinks and semantic links]] — link types compared as association signals
- [[header extraction for token-efficient retrieval]] — the other markup-level token saving, measured at 77.5%
- [[retrieval augmented generation]] — why the retrieval half of this matters at all
