---
aliases:
- display alias
- piped wikilink
- wikilink alias
tags:
- technical
- pkm
- obsidian
---

the piped form of a wikilink, `[[long descriptive note name|short label]]`, is a human display convenience. it shortens what a person reads in a sentence and pays for it in exactly the information a machine reader needs. write the bare full name instead, `[[long descriptive note name]]`, and put alternate names in frontmatter where they cost nothing per mention.

## why the pipe costs a machine reader

the link text is the only thing a reader has about the target until it opens the note. a full name that reads as a claim answers "what is behind this" for free; a short label answers nothing and still costs more tokens than either name alone, because the piped form pays for both strings.

measured across [brain](https://github.com/hannesdelbeke/brain) in [[2026-09-02 what wikilink markup costs a machine reader]]: of 1,735 piped links, the shortening ones keep **40% of the target name's length** on average, so roughly 60% of what the filename already says never reaches the sentence. 227 of them display text identical to the target, paying twice for one string. only 429 make the display text longer than the target, which is the one direction that leaves a machine reader better off.

the `[[folder/note name|note name]]` variant is the same mistake with a path attached: Obsidian resolves name-only links regardless of folder, so the path is pure overhead and it breaks when the note moves.

## the rename argument inverts

the real case for the pipe is that it locks the displayed words in time. Obsidian rewrites `[[old name]]` into `[[new name]]` on rename and edits your sentence under you, where the piped form keeps the prose still.

in a vault where filenames are written as assertions, that protection points the wrong way. renaming the note revises the claim, and a sentence still showing the old label now asserts something the vault no longer believes, with no broken link and no diff to notice it by. the rewrite is the feature: it surfaces every sentence that leaned on the old claim.

## write links this way instead

- bare full name by default, no pipe
- build the sentence around the link rather than bending the link into the sentence
- keep grammar words outside the brackets, `[[header extraction for token-efficient retrieval]] measured 77.5%`
- short forms, acronyms and old titles go in [[Obsidian aliases]] frontmatter, once per note, where they add search surface for free
- if display text must differ, make it longer than the target, never shorter
- the one honest exception is a formal identity a sentence cannot use as a common noun, a person or a product name, and even there restructuring usually beats the pipe

## related notes
- [[2026-09-02 what wikilink markup costs a machine reader]] — the measurements behind this claim
- [[Obsidian aliases]] — the frontmatter feature, which is the good half
- [[wikilink]] — the link form itself
- [[header extraction for token-efficient retrieval]] — the same argument applied to headings, assertion-style beats generic labels
