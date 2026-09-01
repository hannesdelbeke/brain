---
name: research on expertise-location, federated privacy, and home-assistant LLM indexing
description: External research survey for a "network of personal indexes" idea — expertise-finding systems, whether federated/privacy-preserving cross-person search exists, and the current state of LLM-queryable home automation logs
created: 2026-09-01
tags:
  - pkm
  - ai
  - privacy
  - research
  - technical
---

Survey done to evaluate an idea: extending this vault's own indexing techniques ([[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]]'s co-commit mining, cross-encoder reranking, header extraction) beyond a personal notes vault — to a home automation server, code repos, and eventually a cross-person "who has the code/paper for this" network. Evaluation and pitches (which touch private/company specifics) are in a separate private note; this is the external research behind them.

## expertise-location systems

Commercial tools ([Glean](https://sourceforge.net/software/compare/Glean-Search-vs-Guru-vs-Microsoft-Viva/), Guru, Microsoft Viva Topics, [Onyx/Danswer](https://github.com/onyx-dot-app/onyx), Elastic Enterprise Search) mostly surface *documents mentioning a topic*, not *people who know it* — [Stack Overflow Internal](https://stackoverflow.blog/releases/internal/) is the clearest published exception, with an explicit SME auto-assign feature that routes questions to tagged experts and demotes inactive ones over time.

The academic version of this problem has a name and a closed benchmark: the [TREC Enterprise Track](https://trec.nist.gov/pubs/trec16/papers/ENT.OVERVIEW16.pdf) (2005-2008) ranked employees by expertise from email/document corpora; no major follow-up track since. More recent, code-specific work — [CodeCV](https://www.computer.org/csdl/proceedings-article/scam/2022/960900a143/1JSpk9oqpY4) (IEEE SCAM 2022), RepoSkillMiner — mines commit history via topic modeling to infer domain expertise, with **first authorship and recency of modification the strongest measured correlates of real knowledge** (F-score 71-73% with standard classifiers). That recency finding independently matches [[2026-08-31 other candidate relatedness signals for search reranking|this vault's own recency-proximity reranking result]]: recent activity outranks old activity as a relevance signal, in two unrelated domains now.

GitHub's own `CODEOWNERS` is *declared*, not inferred, and [research from 2025](https://arxiv.org/html/2512.05551v2) found declared ownership often diverges from actual commit-frequency ownership while still correlating with faster merge times — evidence that an inferred, evidence-based ownership signal (what [[skills/pkm-metadata-indexer/SKILL|this vault's own co_commit.py]] already computes for wikilink co-edits) is a real, distinct thing from what teams manually declare.

**Known failure modes, documented, not hypothetical:** cold-start (new hires have no commit/document history yet), stale profiles (an expert who left the team still ranks highly on old mentions), and gaming (self-mentioning in docs to inflate perceived expertise). None of these are solved by better ranking math — they're structural to any system built on historical signal.

## does safe cross-person federated search exist

This is the load-bearing question for a "network everyone's personal index" idea, and the answer is close to no.

**Federated search** (querying multiple independent sources in parallel without centralizing data) is real, deployed technology — but it works by each source keeping its own security policy and simply returning results to a coordinator, not by hiding *what* was found from that coordinator.

**Secure multi-party computation** and **differential privacy on search/ranking** are the two techniques that could, in principle, let someone ask "does anyone have X" without exposing anyone's full index or trusting a central party. Both are proven in the research literature. Neither has a turnkey, production-ready deployment for this specific problem — SMPC is computationally expensive at the scale a real search index needs, and differential-privacy-on-ranking is a published trade-off (privacy bought at a measured cost in retrieval quality), not a shipped product.

Personal life-indexing tools that exist today — [Rewind.ai](https://rewind.ai/what-happened-to-rewind/) (shut down Dec 2025, acquired into Meta's Limitless), Microsoft Recall (opt-in after a real privacy backlash over unencrypted snapshots, now TPM-encrypted and biometric-gated), Memex, DocFetcher, Recoll — are uniformly **local-only, single-user**. None ship an opt-in "share a summary with named other people" mode. That gap isn't an oversight; it's the same unsolved problem as the paragraph above.

**Documented cost of getting this wrong:** workplace activity-monitoring research finds a measurable, not hypothetical, harm — 56% of monitored workers report stress vs. 40% unmonitored, 45% report negative mental health impact vs. 29%, and the mechanism named across multiple studies is a **chilling effect**: self-censorship, reduced risk-taking, avoidance of admitting knowledge gaps. This applies even to systems built with good intent, because the harm comes from the *perception* of being tracked, not from any particular technical flaw in how the tracking works.

## home assistant + LLM: commands are solved, history is not

Home Assistant's own [Assist](https://developers.home-assistant.io/docs/core/llm/) voice pipeline plus community add-ons ([Extended OpenAI Conversation](https://extended-openai-conversation.mintlify.app/), Home LLM) handle *commands* well — "turn off the lights" — with a mature local-LLM option (Qwen3 8B recommended for reliable tool-calling).

*Historical* queries are a real, named, currently-unshipped gap: **no native interface exposes Home Assistant's Recorder/history database to an LLM.** A proposal for a whitelisted `HassGetState` intent exists in the project's own architecture discussions but isn't shipped. The community's current workaround is exporting logs into a vector database and doing RAG over them by hand — exactly the same shape of problem [[pkm-search|this vault's own local search daemon]] already solves for notes, just pointed at a different SQLite database (Home Assistant's Recorder, not a markdown vault).

Documented failure modes on the command side, for context: token cost balloons when the full entity list is stuffed into context every turn (one report: 300K+ tokens across 36 API calls), and a longer entity list measurably increases wrong-command execution risk — the same "context bloat costs real money and real accuracy" lesson this vault's own [[token efficient PKM analysis architecture|token-budget research]] already established, in a different domain.

## related
- [[skills/pkm-metadata-indexer/SKILL|pkm-metadata-indexer]] — the co-commit mining, cross-encoder reranking, and header-extraction techniques this survey keeps comparing against
- [[2026-08-31 other candidate relatedness signals for search reranking]] — this vault's own recency and co-occurrence signal research, echoed by the CodeCV finding above
- [[token efficient PKM analysis architecture]] — the token-budget discipline that applies equally to a home-automation history index
