---
name: prior exposure as an implicit edge - the link between recency reranking and code-authorship expertise
description: The same underlying mechanism — prior exposure causally shapes what gets produced next — explains why recency-proximity reranking works as a note-ranking signal and why first git authorship predicts real code knowledge, and this vault already measured why the naive version of that mechanism fails
created: 2026-09-01
tags:
  - pkm
  - ai
  - research
  - graph-theory
  - technical
---

> any note in the past influences all notes in the future, since it alters the mind of the author (or agent) who wrote it — all prior knowledge shapes subsequent action and therefore subsequent discovery. that's a real, if invisible, link between notes, and it looks like the same mechanism as first git authorship predicting who really knows a piece of code.

That comparison holds, and this vault already has evidence on both sides of it, including a proof of exactly how far the naive version of the idea can be pushed before it breaks.

## the same mechanism, two domains

[[2026-08-31 recency-proximity reranking prior tested against real wikilinks|this vault's own recency-proximity research]] traces its origin to precisely this claim: "every note in a vault is latently connected to every earlier note, because one continuous mind wrote all of them" — citing Vannevar Bush's associative trails (*As We May Think*), Niklas Luhmann's Zettelkasten practice, and the cognitive mechanism behind both, spreading activation (Collins & Loftus, 1975): activating one concept in memory partially activates everything associated with it, including things written or read long before, without any explicit pointer between them.

[[2026-09-01 research on expertise-location, federated privacy, and home-assistant LLM indexing|today's separate research]] on code-authorship expertise-finding found the code equivalent from a completely different literature: Montandon et al. (MSR 2019, "Identifying Experts in Software Libraries and Frameworks Among GitHub Users"), refined by [Cury, Avelino, Santos Neto & Valente](https://dl.acm.org/doi/10.1016/j.infsof.2024.107445) (*Information and Software Technology* 170, 2024, 107445), measured that **first authorship is the strongest positive predictor of who actually understands a piece of code, and recency of modification is the strongest negative one** — not the person with the most commits, not the person with the most seniority, and not simply whoever touched the file most recently either, since that turns out to correlate with the *absence* of expertise rather than its presence.

**correction:** an earlier version of this note attributed this finding to CodeCV (IEEE SCAM 2022) and described recency of modification as a second positive predictor running alongside first authorship. both the attribution and the direction were wrong, per [[2026-09-01 adversarial literature check for candidate 3]]: the finding traces to Montandon et al., which CodeCV cites in its own related work rather than originating, and recency of modification is the single most *negatively* correlated variable with measured code knowledge in that dataset — plausibly because whoever most recently touched a file is often the newest person currently learning it or patching someone else's bug, not the person who understands it best.

Same claim, two names: a mind that has been shaped by an artifact (a note, a function, a decision) carries that shaping forward into whatever it produces next, whether or not any explicit trace — a wikilink, a citation, a `git blame` line — records the connection. The link is real and causal; it's just invisible to a graph built only from explicit references.

## this vault already tested the naive version, and it failed

The valuable part isn't the theory, which is old (Bush wrote it in 1945) — it's that this vault already operationalized the naive form of it and measured exactly how it breaks.

The straightforward implementation — every pair of notes gets an implicit edge weighted by how close together they were written, boost ranking by that closeness — was built and tested three ways against real wikilinks (a human, at write time, saying "these two are related," used as ground truth):

- **A global multiplier** on vector-similarity score: every τ (time-decay window) tested made ranking *worse*, from -19.5% MRR at 3 days to -2.3% even at 1000 days. No configuration was positive.
- **Reciprocal rank fusion**, the standard production way to combine relevance and freshness: also rejected, worst at small k (-21% at k=100,000), never positive at any k tested.
- **A small additive term** (`final_score = vector_score + λ·proximity`, not a multiplier): the only form that worked — +7.73% to +8.60% MRR, stable across every random seed tested.

The proof for *why* the first two fail generalizes past this specific vault: a temporal-closeness boost can only demote a true target relative to something *closer in time*, and the number of temporal "rivals" near any given note is large (measured directly: 14.4 other notes within 1 hour of any note, 37.4 within 24 hours) — so the chance that *some* rival gets boosted past the true target approaches certainty as rival count grows, regardless of how the decay curve or fusion constant is tuned. The mechanism is real, but it's diluted by every other note sharing the same rough time window, most of which have nothing to do with the specific pair a human actually linked. An additive term survives because it can only break near-ties — it's structurally incapable of displacing a candidate that was clearly better on content, unlike a multiplier or rank-fusion term, which can be swamped by proximity alone.

## the transferable warning for code-authorship expertise

The same failure mode should be expected, not assumed away, if "who was recently near this code" gets used as an expertise-finding signal the same naive way: a naive proximity boost (whoever touched a file most recently, or whoever's commits cluster closest in time to a change, ranks as most expert) will have exactly the same rival-count dilution problem — many commits near a given file or period share nothing but coincidental timing (a mass reformat, a dependency bump, a build-config change), the same way many notes share a rough creation window without being substantively related.

This vault's [[skills/pkm-metadata-indexer/SKILL|co-commit mining work]] independently found the code-domain version of the same lesson: a raw co-edit weight is dominated by hub files/hub committers unless explicitly excluded (`z_hub_degree`), and lift-normalization (not raw weight) is what correctly demotes a "touches everything" signal in favor of a rare, specific pairing. That's the same shape of fix as the additive-not-multiplicative result above: **don't let a broad, real-but-diffuse signal (temporal or topical proximity) directly rescale a ranking; let it only break ties or act as a bounded, small correction on top of a stronger underlying signal (content similarity, actual co-edit weight).** Any future expertise-finder built on "recent activity near this code" should assume it needs the same additive, hub-excluded shape as both signals here, not a proximity multiplier, and should test for the same rival-count dilution before trusting a raw version of the idea.

## a direct measurement, not just a literature comparison

the transfer claim above was argued from CodeCV's own numbers. it can be checked more directly: the rank-flip proof's actual precondition is rival *density* — enough other things happening close in time to any given anchor that a naive proximity boost gets swamped by them, whatever the domain. that's measurable against real commit history without needing any labeled "who's the real expert" ground truth. measured against this vault's own two git repos: mean rivals within 1 hour / 24 hours of any given commit are 22.00 / 169.38 in one repo and 7.28 / 57.04 in the other — both the same order of magnitude as the 14.4 / 37.4 notes-per-window that made the multiplicative failure mode near-certain for note reranking. the precondition transfers; a full replication of the MRR result itself would still need a real labeled expertise dataset (CodeCV's own, or a new one), which this check doesn't provide.

## established prior art for git-mined expertise

code-authorship-from-git-history is not a new idea — it's a well-established practical tool category, beyond CodeCV and generic `CODEOWNERS`. [code-maat](https://github.com/adamtornhill/code-maat) (2,600+ stars, verified 2026-09-01, actual 2,626) mines VCS history for ownership, knowledge distribution, and coupling, with an explicit "entity-ownership" analysis mapping directly to "who really knows this code." [hercules](https://github.com/src-d/hercules) (2,800+ stars, verified 2026-09-01, actual 2,808) does the same via `--burndown-people` (confirmed in its README), tracking whose lines get overwritten by whom as a proxy for expertise teams. [git-ownership](https://github.com/MichaelMure/git-ownership) (verified 2026-09-01) is a smaller tool visualizing surviving-lines-per-author over time. [reviewers-by-blame](https://github.com/DolceTriade/reviewers-by-blame) (a Gerrit plugin, verified 2026-09-01) and [git-suggest-reviewer](https://github.com/ccntrq/git-suggest-reviewer) (verified 2026-09-01) go further, recommending a *specific* reviewer for a *specific* change by blame-weighted authorship — the exact granularity CodeCV's own claim operates at, not whole-repo ownership stats. These tools already assume the practice this note argues for from theory — the rank-flip proof and the rival-density measurement above explain *why* their design choices (ownership from sustained authorship, not from raw recent-touch counts) work, rather than introducing the practice itself. Worth citing as established, independently-arrived-at practice that this note's theory now has a mechanistic explanation for.

Notably, none of the co-commit/logical-coupling tools checked (Hercules, code-maat, and smaller tools like `LogicalCouplingTool`) document filtering out **hub nodes** — a file touched in nearly every commit (a build config, a shared utility) that pollutes a co-occurrence signal with noise. This vault's own [[skills/pkm-metadata-indexer/SKILL|co-commit mining work]] already ships that fix (`z_hub_degree` exclusion, lift-normalized co-occurrence) — on the evidence of this search, that's a real, unaddressed gap in existing open-source tooling, not a rediscovery.

## related
- [[2026-08-31 recency-proximity reranking prior tested against real wikilinks]] — the full experiment, proof, and the additive-form recommendation this note builds on
- [[2026-09-01 research on expertise-location, federated privacy, and home-assistant LLM indexing]] — the CodeCV first-authorship finding
- [[2026-09-01 adversarial literature check for candidate 3]] — found and corrected this note's misattributed, direction-reversed CodeCV/Montandon citation
- [[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]] — the co-commit hub-exclusion and lift-normalization result this note draws the parallel to
- [[2026-08-31 wide time gaps between repeated notes are stronger signal than close ones]] — a related but distinct use of time-gaps-as-signal in this vault: confidence in a recurring pattern rather than relatedness between different notes
