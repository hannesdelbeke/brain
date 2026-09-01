---
name: hop-ceiling pilot - a u-curve shadow the token-ceiling test never found
description: a 3-trial pilot testing whether limiting an agent to one note per turn (no accumulated context) reproduces a position effect that the single-shot concatenated-document test could not, on the same fact and question
created: 2026-09-01
tags:
  - pkm
  - research
  - readability
  - llm
  - lost-in-the-middle
  - experiment-design
---

> [!summary] eli5
> the earlier pilot fed a model 13 documents all at once and asked a question — 3/3 correct, no dip, at any position. this pilot asks the same question about the same fact, but shows the model one note per turn instead, with no memory of earlier notes except its own running sense of the task. result: correct, wrong, correct — hop 4 (the middle) got a real, different tool name wrong, not just "not stated." a small, real signal the token-ceiling version never produced.
> done, n=1 per position, real signal but too small to trust alone.
> **needs from you:** decide whether to repeat this design with more instances per hop-position (recommend yes — 3-5 repeats per position, same 7-hop structure, before treating "middle hops are harder" as a real finding rather than one lucky/unlucky trial).

**why:** [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]]

## the idea this tests

a [conversation earlier today] raised a sharp point: if an agent traversing a graph (or a multi-turn conversation) gets to see every previously-visited node stacked in its context, "hop distance" and "token distance" are the same variable — a bigger context window just lets a model swallow more hops per glance, so what took 10 hops on a small-context model takes 1 hop on a big-context one. that would mean a hop-ceiling test is just a token-ceiling test wearing a different name, and would explain why the single-shot document pilot found nothing: the model could just re-read all 13 documents at once regardless of where the target sat.

the fix: strict amnesia. each turn shows *only* the current note — no running transcript of earlier notes stays in view except whatever the model itself carries forward as its own memory of the task. that's not a context-window test anymore. it's a test of whether a model's grip on the original goal degrades over a long sequence of small decisions, independent of how much any single decision can hold. a bigger context window doesn't obviously fix that.

## setup

same target fact and question as [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]]: the note describing an all-steel right-angle checking tool ("machinist square" / "engineer's square"), question worded with zero vocabulary overlap ("for checking a perfect right angle, craftspeople often pick an all-metal option over the older wood-bodied version because it holds its accuracy better over time. what is that all-metal tool called?").

three fresh claude/haiku subagents, each resumed turn-by-turn via direct messages (not re-sent full history — each turn's message contained only the next note's text plus the standing instruction to answer or say "next"). same 6 distractor notes as the earlier pilot (rocket stove, instagram-as-diary, youtube premium, river tame, roller shutters, maya node editor), 7 slots total, target inserted at slot 1, 4, or 7 across the three trials, everything else identical and in the same order.

## result

| hop position | answer given | correct? |
|---|---|---|
| 1 (start) | "Engineer's square" | yes |
| 4 (middle) | "Speed Square" | **no** |
| 7 (end) | "Engineer's square" | yes |

correct, wrong, correct — a shape the single-shot 13-document pilot never produced (that one went 3/3, flat, no dip at any position). the hop-4 error is a genuine confusion, not a refusal: "Speed Square" is a real carpentry tool (a triangular layout square), a plausible-sounding wrong guess rather than "not stated," suggesting the model's sense of which fact it was chasing had drifted by the fourth turn rather than simply forgetting it saw one.

## what this does and doesn't show

**does show:** a real, observable difference between the two designs on the identical fact and question — turn-by-turn delivery produced an error the same content, delivered as one block, did not. that's at least consistent with the idea that hop-count and token-count are measuring different things when context is genuinely restricted per turn.

**doesn't show:** that "middle hops are harder" is a real, general effect. this is n=1 per position — one wrong answer at one position could easily be noise (a single bad rephrasing, one moment of model confusion) rather than a real curve. the single-document pilot only became trustworthy after being run at n=2-6 per cell across several scales; this pilot hasn't earned that yet.

## next step

repeat with more instances per position (3-5 per hop, same 7-hop structure, fresh content each time so the specific fact/note pairing isn't doing the work) before citing "hop distance degrades accuracy independent of token budget" as a real finding. if the middle-hop error rate stays elevated across repeats, that's a genuinely new, distinct claim from anything in [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] or [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — both of those are about position *within a single context*, not persistence of a goal *across turns*.

## related

- [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]] — the single-shot pilot this one contrasts with, same fact and question
- [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]] — the diagnosis this pilot is an alternative angle on
- [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] — the original liu-et-al-scale design, still the next step for the single-shot line of testing
