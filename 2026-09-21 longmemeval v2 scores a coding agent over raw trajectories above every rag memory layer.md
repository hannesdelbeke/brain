> [!summary] eli5
> longmemeval is the benchmark people cite when they claim an ai memory product works, and this note says what it actually measures, what its own authors found out about memory design, and how far apart the two scores quoted for mem0 are.
> researched and written, nothing acted on: the benchmark's second version moved from chat history to web-agent trajectories and found that a coding agent reading raw files beats every retrieval-based memory layer, which is the same shape [[2026-09-21 mem0 v3 stopped reconciling contradictions at write time]] already argued for on other grounds.
> **needs from you:** decide whether the mem0 note's 49% longmemeval figure gets mem0's own 94.4% put beside it as a labelled vendor claim, recommend yes and a one-line edit, because that note currently reads as though 49% is the settled number when neither figure has an independent grader behind it

> longmemeval tell me more
> — and: write note on it's own linked to the mem0 note

**why:** [[2026-09-21 mem0 v3 stopped reconciling contradictions at write time]]

## longmemeval v1 measures five memory abilities and long-context models lose 30 to 60 percent on it

[longmemeval](https://arxiv.org/abs/2410.10813) is 500 questions over synthetic chat histories, built by di wu and colleagues and published at iclr 2025, testing information extraction, multi-session reasoning, temporal reasoning, knowledge updates and abstention.
the last two are the ones older benchmarks skipped: knowledge updates asks whether a system uses the fact the user revised rather than the one they first gave, and abstention asks whether it says "not in the history" instead of inventing an answer.
it also scores recall of what the assistant said, not only what the user said, which msc and locomo both leave out.

the standard configuration runs about 115k tokens of history per instance and the large one goes to 500 sessions and roughly 1.5m tokens, consumed in order before the question arrives.
against that, long-context models drop 30 to 60 percent relative to being handed only the relevant session, and a much easier manual evaluation put commercial assistants including gpt-4o at 30 to 70 percent.
the failure modes named are lost-in-the-middle, failure to aggregate facts scattered across sessions, and shallow pattern matching on the query terms.

## round-level storage beat both session-level and fact-level chunking in longmemeval's own ablations

the more useful half of the paper is the framework rather than the leaderboard, because it splits memory into indexing, retrieval and reading and then ablates each one.
the storage-granularity result is the transferable one: a single conversational round is the best unit, a whole session is too coarse, and compressing further into extracted atomic facts makes overall accuracy worse while making multi-session reasoning better.
that is an argument against fact extraction as a default and for keeping the source text addressable, which is the same trade [[2026-08-18 what retrieval costs as a vault grows]] reaches from the cost side and [[vault hybrid search]] already implements by indexing heading sections that still carry their links.

two indexing tricks in the paper are cheap enough to be worth remembering: expanding the index key with facts derived from the chunk, and expanding the query with a time range when the question is temporal.

## reading retrieved context loses more accuracy on longmemeval than retrieving it does

even when the correct items are placed in the context by construction, models still get the answer wrong, and the paper measures the gap rather than assuming retrieval is the bottleneck.
chain-of-note prompting and structured json output recover up to 10 absolute points across three different models on the same retrieved context.
the practical reading is that a memory system evaluated only on recall@k is being scored on the easier half of its job.

## longmemeval v2 moved from chat sessions to web-agent trajectories at 115m tokens per instance

[longmemeval v2](https://arxiv.org/abs/2605.12493), posted may 2026 by the same lead author, keeps the five-ability structure but replaces chat history with agent trajectories from webarena, workarena and workarena++, and reframes the abilities as static state recall, dynamic state tracking, workflow knowledge, environment gotchas and premise awareness.
it is 451 manually curated questions over histories of up to 500 trajectories and 115m tokens, and the framing is whether memory can turn an agent into a colleague who already knows the environment.

v2 has not replaced v1 and vendors do not report against it, so a bare "longmemeval score" in marketing copy in 2026 is v1 and almost certainly the 115k-token configuration.
its [project page](https://xiaowu0162.github.io/longmemeval-v2/) ranks entries by an accuracy-versus-latency frontier metric rather than by accuracy alone, which is unusual and is there because the winning method is slow.

## a coding agent reading raw trajectory files beat every rag memory layer on longmemeval v2

the headline v2 result is that storing trajectories as plain files and pointing a coding agent at them in a sandbox scores 72.5 percent average, against 48.5 percent for the strongest retrieval-based baseline.
an off-the-shelf coding agent with no memory design at all scores 69.3 percent, so nearly all of the gap is the agent being able to search and read the raw material rather than anything the memory layer contributed.
the cost is latency: the coding-agent methods take 140 to 186 seconds per query where retrieval methods finish under 30, which is why the leaderboard scores the frontier instead of the peak.

that result points the same way as the mem0 conclusion in [[2026-09-21 mem0 v3 stopped reconciling contradictions at write time]], from an independent direction.
a memory layer that extracts facts into its own store competes with, rather than adds to, a capable reader given good search over the original text, and on v2 it loses by 24 points.
the caveat worth keeping is that v2's environment-gotchas category stays under 52 percent for every entry including the winner, so the hardest thing a colleague knows is still the thing no method has learned to carry across trajectories.

## the two longmemeval scores quoted for mem0 differ by 45 points and neither has an independent grader

mem0's own [2026 benchmark writeup](https://mem0.ai/blog/ai-memory-benchmarks-in-2026) reports 94.4 percent on longmemeval, alongside 92.5 on locomo and 64.1 on beam-1m.
the single non-vendor figure already recorded in [[2026-09-21 mem0 v3 stopped reconciling contradictions at write time]] puts the same product at 49 percent against a 60.2 percent full-context baseline.
those cannot both describe the same measurement, and the resolution is not available from outside: the two runs differ in subset, reader model and grader, and none of the three is pinned by the benchmark itself.

the honest position is that no independent longmemeval number for mem0 has been published, rather than that either figure is the true one.
v1 has also been public since october 2024 with a fixed set of 500 questions, so a 2026 score in the mid-nineties on it carries less information than the same score would have carried in 2025, whoever produced it.
