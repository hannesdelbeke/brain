---
name: process log - from readability question to publish plan
description: how a question about text-structure research turned into a gap analysis, a code change, and a publish plan, and what each step actually found
created: 2026-09-01
tags:
  - pkm
  - research
  - meta
  - process
---

> log the whole process in a separate note

## step 1: why is academic writing hard to read

started from a plain research question, not a vault-specific one: what makes text structure easier or harder to read, and why do most papers fail at it. found [Plavén-Sigray et al. 2017](https://elifesciences.org/articles/27725) (measured readability decline across 707k biomedical abstracts, 1881-2015), [Gopen & Swan 1990](https://www.usenix.org/sites/default/files/gopen_and_swan_science_of_scientific_writing.pdf) (old/new information misplaced in a sentence is the core structural fault), and [Pinker 2014](https://www.chronicle.com/article/why-academics-stink-at-writing/) (curse of knowledge, status-defensive prose, weak incentives). while confirming the two LLM-attention papers already cited in the CLAUDE.md global instructions, found one was mislabeled: arXiv:2411.10541 is He et al. 2024's prompt-formatting study, not the paper the note's phrasing implied. fixed directly in `C:\Users\H\.claude\CLAUDE.md`.

## step 2: the vault already had this research, further along than expected

before writing anything new, searched the vault per [[AGENTS.md|its own convention]] and found four existing public notes already doing exactly this kind of work: [[2026-08-30 readability and reading-speed research applied to note-taking vaults]] (human-reading research applied to notes), [[2026-08-30 agent reading versus human reading, which formatting rules transfer]] (which rules hold for an LLM reader and why), and a second, unrelated-looking cluster — [[2026-08-31 research on compressing llm reasoning and notes without losing information]], [[2026-08-31 classifier-based compression with an adversarial fidelity gate]], [[2026-09-01 note-compress skill - design, adversarial review, and bench data]] — that turned out to be the stronger material: a real empirical comparison (two-pass classify-and-score method vs. a rule-based compressor, benchmarked on real notes) plus a live-corpus test against 151 eligible notes.

## step 3: added the missing writer-side research

the vault's existing readability notes covered the reader's side (how a reader extracts meaning fast) but not the writer's side (why prose gets hard to read while being written). wrote [[2026-09-01 why academic writing is hard to read]] to close that, linking Gopen & Swan's sentence-scale rule to the vault's own heading/bullet-scale rule, and Chandler & Sweller's split-attention effect to the vault's evidence-placement practice.

## step 4: two parallel research forks found the actual gaps

ran two research questions in parallel rather than sequentially, since neither depended on the other:

- **literature gap:** the vault's adversarial fidelity gate (one agent compresses, a second independently scores what survived) is structurally identical to **LLM-as-judge**, a named technique with known reliability problems the vault had never connected to. [Zheng et al. 2023](https://arxiv.org/abs/2306.05685) named position and verbosity bias; ["Rating Roulette" (2025)](https://arxiv.org/html/2510.27106v1) measured exactly the non-determinism the vault caught live (same prompt, same note, one call passed and one mangled a fenced code block) and gave the fix — run the judge multiple times, average, don't force temperature=0. also surfaced a still-open gap this vault's mechanical checks can't catch: "relinking" (KBRA, [arXiv:2606.21732](https://arxiv.org/html/2606.21732)), individually-true fragments reassembled into a false claim. written up in [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]].
- **publish venues:** arXiv tightened its endorsement policy in January 2026 (no more auto-qualification via institutional email), making it a slow first move for an unaffiliated author. [Workshop on Insights from Negative Results in NLP](https://insights-workshop.github.io/) (EMNLP 2026, Budapest, Oct 22–29) is a strong direct fit for the compression benchmark's negative result (link/number density doesn't predict compressibility). the readability synthesis is a better fit for a blog post cross-posted to LessWrong/Alignment Forum than for a formal venue, since it's synthesis with one original framing rather than a novel measured result.

## step 5: closed one gap in the running code, left one open

delegated a scoped code change to [[skills/note-compress/SKILL|note-compress]]: an opt-in `--audit-sample N` flag that runs the framing-fidelity judge 3 times per sampled note and averages, per the Rating Roulette finding. this addresses the framing-drift blind spot the mechanical gate structurally cannot catch. it does not address relinking — that's recorded as an open limitation in the gap-analysis note and the publish plan, not silently dropped.

## step 6: publish plan

wrote [[2026-09-01 publish plan - readability and compression research as papers]] ranking the two clusters, naming what's still missing before either is submittable (a second model run and an explicit relinking limitation for the compression study; an actual experiment instead of argued-from-mechanism reasoning for the readability synthesis), and a venue plus concrete next steps for each.

## step 7: a re-sweep found a third cluster, and why the first pass missed it

asked why the first pass didn't surface [[2026-09-01 prior exposure as an implicit edge - the link between recency reranking and code-authorship expertise]] and [[2026-09-01 research on expertise-location, federated privacy, and home-assistant LLM indexing]]. two real reasons, not one: topic mismatch (the original searches were scoped to "readability" and "compression," an unrelated research thread on search reranking and expertise-finding wouldn't surface for those queries regardless of timing), and index staleness ([[search_vault.py]]'s semantic index for `brain` was last built at 09:45:41; both of those notes were committed at 10:12 and 10:43, after that snapshot, so they weren't in the index when the first searches ran even if the query had matched).

a follow-up re-sweep — `git log --since` across both repos for everything touched today, plus a grep across `public/` for every 2026-08-30 through 2026-09-01 note mentioning compression or tokens — found two more real misses:

- [[2026-08-31 other candidate relatedness signals for search reranking]], committed *before* the first pass's index snapshot and missed anyway because no search that day was scoped to search-reranking topics. this one substantially strengthens candidate 3: it tests five more relatedness signals across **four separate vaults** (this one plus three public Obsidian vaults), closing the single-corpus gap the publish plan had originally flagged as missing, and documents a same-session self-correction (an early claim about co-commit's overlap percentage didn't hold up under later, more careful measurement, and was logged as wrong rather than quietly fixed).
- [[2026-09-01 does git history benefit from token compression for an agent]] — directly adjacent to the compression research cluster (asks the same question about git history instead of notes, finds it mostly doesn't apply because commit messages are already terse) but never surfaced by the original compression-scoped searches either, since its own title and content use "git" and "version control" vocabulary rather than "compression" as the leading terms. added as related work on the gap-analysis note.

candidate 3's writeup and venue recommendation were both revised upward on the strength of the four-vault result: from "workshop, on the negative results alone" to "aim for a short paper at an IR venue (ECIR/SIGIR) first, workshop as fallback."

the honest limit of this second pass: it covered everything changed today plus a keyword grep over the two days most relevant to this thread, not a read of all ~3,228 notes in the vault. a genuinely exhaustive pass isn't a reasonable ask at that scale; the practical mitigation is the same one this vault's own search-reranking research is busy improving — a better relatedness signal, not a human or agent reading everything by hand.

## what stayed private

nothing from `private-vault` root (the private half of this vault) was quoted or referenced in any of the public notes above — vault-b-specific brainstorm notes and internal application details stayed out, per the vault's own [[AGENTS.md|brain rule]]. everything above lives in `public/`.

## related

- [[2026-09-01 publish plan - readability and compression research as papers]]
- [[2026-09-01 the adversarial fidelity gate is llm-as-judge, and that literature explains the non-determinism]]
- [[2026-09-01 why academic writing is hard to read]]
