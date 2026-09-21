> [!summary] eli5
> mem0 and letta are memory layers you can bolt onto an agent so it remembers things between sessions, and this note works out whether either one is worth adding here.
> researched in full, nothing installed: mem0's newest version deliberately removed the contradiction-handling that was the reason to want it, letta cannot sit under claude code at all, and the retrieval half of what mem0 sells is already running locally in this vault.
> **needs from you:** decide whether [[2026-08-27 Mem0 memory architecture - cloud pricing, security, and local privacy]] gets corrected, recommend yes and a one-line edit, because it currently tells a reader that mem0 "automatically updates or invalidates the conflicting older record" and that stopped being true

> how could we use mem0 or memgpt in this pkm or workflow? and would it hallucinate? currently notes written by agents sometimes hallucinate so verification and reviews afterwards end up with good result over time. mem0 seems cool but would it add value. also search similar notes. or online
> — and, on the first draft of this answer: i thought the whole point of mem0 was this contradiction technique. strange they don't have it.

**why:** [[2026-08-27 Mem0 memory architecture - cloud pricing, security, and local privacy]]

## mem0 removed write-time contradiction handling on purpose, and that was the feature worth having

the suspicion was right that this deserved checking, and the answer is that mem0 really did drop it. the [original paper](https://arxiv.org/abs/2504.19413) describes a two-phase pipeline whose second phase is an llm deciding between four operations, "ADD for creation of new memories, UPDATE for augmentation of existing memories, DELETE for removal of memories contradicted by new information, NOOP when the candidate fact requires no modification". that is the reconciliation everyone means when they say mem0 handles contradictions.

the current platform does not do it. mem0's own [v2 to v3 migration note](https://docs.mem0.ai/migration/platform-v2-to-v3) puts the before and after side by side, "memory mutations: ADD, UPDATE, DELETE" becoming "ADD only: nothing is overwritten or deleted", and says plainly that "the previous algorithm could UPDATE or DELETE existing memories during extraction. the new algorithm only adds new facts." the [engineering writeup](https://mem0.ai/blog/mem0-the-token-efficient-memory-algorithm) gives the consequence: "every extracted fact becomes an independent record. when information changes, the new fact lives alongside the old one."

the honest reading is that the job moved rather than vanished. v3 keeps both facts with temporal context and sorts it out at retrieval with recency and multi-signal ranking, which buys roughly half the write latency. but it is a genuinely weaker guarantee: reconciliation now has to succeed on every single read instead of once at write, nothing is ever repaired, and there is no artifact anywhere that says which of two conflicting facts won. a note updated in place has answered that question permanently, in a diff.

## the retrieval half of mem0 is already running here, so buying it adds a dependency and no capability

what mem0 sells for the read path is embeddings plus a ranker over extracted facts. [[vault hybrid search]] already fuses bm25 over sqlite fts5 with bge-small embeddings by reciprocal rank fusion, [[semantic search]] shows the embedder resolving wikilinks rather than choking on them, and [[eval_related.py]] and [[search_vault.py]] cover similar-notes and query against 3,206 notes and 8,654 heading sections in this repo alone, on cpu, offline, with no api key and no per-search quota.

[[2026-08-18 what retrieval costs as a vault grows]] already put the ceiling on this: no vector database is warranted below roughly 300k notes. mem0 would be a second index of the same content, with a worse unit of retrieval, because it indexes extracted sentences while this vault indexes heading sections that still carry their source and their links.

## the thing mem0 would actually add is a place for hallucinations to live below the review layer

this is the part that answers the question directly, and it is not a hypothetical. mem0's [state of agent memory writeup](https://mem0.ai/blog/state-of-ai-agent-memory-2026) lists as a feature that "mem0 now treats agent-generated facts as first-class" — the model's own output is stored with the same standing as something you said.

a hallucinated note today is a file, with a heading, in git, reachable by search, and read by a human eventually. that is why the verification-and-review loop converges: every property the loop needs is present. a hallucinated mem0 record has none of them. it arrives through a second lossy extraction pass, so it is not even the sentence the agent wrote, it carries no anchor back to the conversation that produced it, it is now un-deletable by construction, and there is no diff to review because there was never a file. the vault's failure mode is a wrong paragraph you can see. mem0's is a confident sentence retrieved months later with no provenance and no correction path.

## letta is a runtime, not a library, so it is not installable here at any price

letta, the former memgpt, is not a memory layer you add to an agent. it is the agent, with core, recall and archival tiers that the model edits through tool calls, and the model runs inside letta's loop. claude code cannot run inside it, which makes the integration question moot before any of the memory design matters. the official letta obsidian plugin also syncs the wrong way, pushing vault content into letta rather than letting letta write notes. [[2026-08-29 agentic memory - scoped devlogs vs monolithic memory]] already rejected the monolithic memory shape on independent grounds.

## the published comparisons are vendor-sourced almost without exception, including the ones that look independent

mem0's headline "+26% over openai memory" is self-reported and has not been independently replicated. locomo, the benchmark it rests on, ships questions without a canonical grader, so each vendor scores its own runs, which is how the [zep and mem0 dispute](https://github.com/getzep/zep-papers/issues/5) got as far as it did. one non-vendor comparison puts mem0 at 49% on longmemeval against a 60.2% full-context baseline, though that is a single medium post and should be held loosely.

the [reddit thread comparing mem0, zep and supermemory](https://www.reddit.com/r/AIMemory/comments/1qbmffy/i_tried_to_make_llm_agents_truly_understand_me/) is a good illustration rather than a good source. the author is building a competing product and links it in the comments, the zep founder turns up to correct a factual error about zep in the post, and a drive-by commenter claims another vendor "scored 90.1% on the locomo benchmark making them the fastest and smartest ai memory". the useful signal in it is not any number.

## the people who did solve contradictions all landed on supersede-not-overwrite in a relational store

the practitioners in that thread converge, and none of them converge on mem0's answer. one reports implementing zep's bi-temporal model — which records both when a fact was true and when the system learned it — "on sqlite instead of neo4j", where "facts get superseded rather than overwritten, and retrieval defaults to currently-valid knowledge". another, building multi-agent shared memory, says flatly that "the conflict resolution problem is still the hardest part honestly" and that "temporal weighting helps (newer facts score higher) but it's not solved" — which is exactly the mechanism v3 now depends on, described by someone using it as insufficient.

two things follow. the supersede pattern is the right shape for a contradiction check here if one is ever built, on sqlite, against the sections already indexed, flagging conflicts at write time rather than silently picking a winner at read time. and the vault's existing habit of editing a note in place is already the strong version of that pattern, done by hand: the old claim is gone, the new one is current, and the history is in git rather than in a ranker's tie-break. building the automated version is deferred by decision on 2026-09-21, not blocked — [[2026-08-27 agentic pkm action plan]] and [[progress - agentic biomimetic vault]] hold the other deferred memory items it would join.
