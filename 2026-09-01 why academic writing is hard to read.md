---
name: why academic writing is hard to read
description: research survey on why scientific and academic prose is hard to read and getting harder, as the writer-side counterpart to the vault's reader-side readability research
created: 2026-09-01
tags:
  - pkm
  - readability
  - writing
  - research
---

> research on text structure, readability, and ease of understanding — why most papers fall foul of things that make them harder to read

[[2026-08-30 readability and reading-speed research applied to note-taking vaults|the readability research]] already in this vault covers the reader's side: scanning, chunking, the F-pattern, what structure lets a reader extract meaning fast. This note covers the other side — why academic and technical prose gets hard to read while it's being written, which is a distinct, well-studied problem with its own causes.

## the decline is measured, not just felt

[Plavén-Sigray et al. 2017, "The Readability of Scientific Texts Is Decreasing Over Time"](https://elifesciences.org/articles/27725) (eLife) scored 709,577 biomedical abstracts from 1881 to 2015 and found readability falling steadily, driven mainly by rising jargon density ("moreover," "underlying," "robust," "suggesting") rather than sentence length alone, though sentence length has also crept up since the 1960s. Over 20% of abstracts now score beyond college-graduate reading level, and the effect holds in full papers, not just abstracts.

## two causes, from two different angles

[Gopen & Swan 1990, "The Science of Scientific Writing"](https://www.usenix.org/sites/default/files/gopen_and_swan_science_of_scientific_writing.pdf) (American Scientist, verified 2026-09-01) locates the single most common structural fault: a reader expects old, context-setting information at the front of a sentence (the "topic position") and new, emphasized information at the end (the "stress position"). Writers violate this constantly because they write sentences in the order ideas occur to them, not the order a reader needs them, and never revise for the mismatch. This is the sentence-scale version of the same instruction [[2026-08-30 readability and reading-speed research applied to note-taking vaults|the vault's note]] already gives at heading and bullet scale: put the subject first.

[Pinker 2014, "Why Academics Stink at Writing"](https://www.chronicle.com/article/why-academics-stink-at-writing/) (Chronicle of Higher Education, expanded in *The Sense of Style*, verified 2026-09-01) names three causes that are about the writer, not the sentence: the curse of knowledge (an expert can't model what a reader doesn't already know, so shorthand natural to the writer reads as jargon to everyone else), status-defensive prose (complexity as a signal of expertise), and weak incentives (reviewers and journals rarely select for clarity).

## where it overlaps with note-structure research

[Chandler & Sweller 1991/1992](https://www.researchgate.net/publication/232474857_Cognitive_Load_Theory_and_the_Format_of_Instruction) (verified 2026-09-01), the split-attention effect from Cognitive Load Theory: forcing a reader to mentally integrate two separated sources — a claim and the figure or data it refers to — burns working memory as pure overhead that disappears once the two are physically placed together. This is the same failure mode as a note that states a conclusion in one section and its supporting numbers in another, or a paper whose results table is a page away from the sentence interpreting it.

Schriver 1997, *Dynamics in Document Design* (checked against secondary sources describing the book, not the 1997 text itself, unverified), reviewed readability formulas (Flesch-Kincaid and similar, which score on syllable and sentence-length counts alone) and found them unreliable predictors of whether a reader actually understands a text. Her conclusion — usability testing, does the reader actually get it, beats a formula score — is the same standard [[2026-09-01 note-compress skill - design, adversarial review, and bench data|this vault's own compression bench data]] already uses: a mechanical fact-check plus a real reader (or an adversarial LLM judge) checking for lost meaning, not a word-count or syllable metric.

## what this adds to the vault's existing rules

the reader-side rules already in place (front-load subjects, chunk to four or five, lede first) are necessary but not sufficient — they fix how a note is organized, not whether an individual sentence buries its own point. two additions worth carrying into note-writing:

- **check topic/stress position per sentence**, not just per heading — old information first, the new or important fact last, the same instruction Gopen & Swan give at paragraph scale
- **never separate a claim from its evidence** — a number, table, or link that supports a sentence belongs next to it, not in a different section, per the split-attention effect

## a real, established fix already exists: the plain-language summary

academic writing's hardness isn't only diagnosed in the literature above, it has a genuine, widely-adopted institutional countermeasure: a short, jargon-free summary published alongside (not instead of) the technical abstract. this is not a fringe practice. [Cochrane systematic reviews](https://training.cochrane.org/plain-language-summaries) require a **Plain Language Summary** on every review (verified 2026-09-01). [eLife](https://elifesciences.org/inside-elife/85518309/plain-language-summaries-how-to-write-an-elife-digest) runs a "digest" rewriting a paper's core finding in accessible language, published right below the abstract — every paper got one until 2016, when submission volume forced eLife to cap it at roughly 60 selected papers a month instead of all of them. [PNAS](https://www.pnas.org/author-center/submitting-your-manuscript) requires a **Significance Statement** aimed at a broad scientific readership, distinct from the technical abstract (verified 2026-09-01). Funders increasingly mandate this too — NIH, the Wellcome Trust, and UKRI all require lay summaries on grant outputs.

the convention that makes it work: never replace the technical abstract, which reviewers and specialists still need at full precision, add the plain-language version alongside it, clearly labeled so nobody mistakes one for the other. for a self-published paper specifically — no venue, no press office writing a summary for you — this does real work: it's what makes a stranger on arXiv or a blog actually read past the title, and it's the exact same lede-first, plain-language principle this vault's own reader-side readability research already argues for, just applied to a paper's audience instead of a note's. this vault's own note convention (every note opens with an eli5 callout) already does this natively — carrying it into a paper draft is not inventing a new practice, it's applying an existing one to a new document type.

## related

- [[2026-09-01 candidate 3 paper draft outline]] — a live example: this practice added to a real paper draft in this vault
- [[2026-08-30 readability and reading-speed research applied to note-taking vaults]] — the reader-side research this note extends to the writer's side
- [[2026-08-30 agent reading versus human reading, which formatting rules transfer]] — which of these rules hold for an LLM reader and which don't
- [[2026-09-01 note-compress skill - design, adversarial review, and bench data]] — the vault's own usability-test-over-formula standard, applied to compression rather than authoring
