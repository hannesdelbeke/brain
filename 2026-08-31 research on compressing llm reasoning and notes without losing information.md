> find research on tips to make llm more efficient, e.g. telling it to use shorter language, see e.g. caveman skill. wonder if agents can think shorter too, without losing the message. and the same for writing to a pkm vault, most notes are agent read only, some are human view. if notes can get shorter without losing info via a skill, worth doing. anyone doing research on this?

there is real research on this, not just prompt-engineering folklore, and it draws a hard line between two different things: shortening a model's own reasoning, and shortening a document a model has to read later.

## shorter reasoning has a measured floor

["how well do llms compress their own chain-of-thought?"](https://arxiv.org/html/2503.01141v1) (2025) tested 31 compression styles across six models on math reasoning. every style, "be concise," bullet points, a word limit, lands on the same length-accuracy curve. what predicts accuracy is token count, not phrasing. each task has an intrinsic **token complexity**, a minimum number of tokens below which accuracy falls off a cliff regardless of how the instruction is worded.

[tale, token-budget-aware llm reasoning](https://aclanthology.org/2025.findings-acl.1274/) (acl findings 2025) acts on that: give the model an explicit token budget scaled to problem difficulty rather than a fixed style, and it cuts chain-of-thought tokens with only a slight accuracy loss.

[sketch-of-thought](https://arxiv.org/abs/2503.05179) (emnlp 2025) is the closest published relative of a caveman-style skill: a cognitive-shorthand reasoning format that cuts reasoning tokens up to 84% with little accuracy loss, because it changes the structure of the reasoning, not just the prose density.

the practical read: a "think shorter" instruction for an agent is safe down to some task-dependent floor, and past that floor it starts dropping information, not just words. a fixed style like caveman doesn't know where that floor is for a given task.

## shorter documents is a different, better-solved problem

[llmlingua](https://arxiv.org/html/2310.05736v2) (microsoft, emnlp 2023) and [llmlingua-2](https://llmlingua.com/llmlingua2.html) compress prompts and documents for a downstream model to read, which is the pkm note case, not the live-reasoning case. llmlingua-2 reframes compression as token classification: a small model learns which tokens carry information and drops the rest, rather than freeform rewriting. result: up to 20x compression with about a 1.5 point performance drop, and gpt-4 could reconstruct the original meaning from the compressed version.

that is the evidence that "shrink a note without losing the message" is a solved shape of problem, classify essential tokens and cut the rest, not a vague aspiration.

## applying it to the vault

for **agent-read-only notes**, this is the target: a compression pass modeled on llmlingua-2's classification idea rather than a plain "make this shorter" prompt, keep facts, links, frontmatter, and any decision the note records, cut connective prose. worth prototyping as a skill, scored on whether a reader (or agent) can reconstruct the original facts from the output, not on token count alone.

for **human-view notes**, none of this research applies directly, it's all measuring llm-to-llm parsing, not human reading speed, so the existing [[2026-08-30 readability and reading-speed research applied to note-taking vaults]] rules should keep governing those, not this.

for **agent reasoning length** (how much an agent thinks before answering), a fixed terse style has a ceiling it can't see: the token complexity floor is per-task, so a caveman-style instruction that works on one task can start cutting real content on a harder one. if this matters enough to tune, the tale-style approach, sizing the budget to the task rather than fixing the style, is the documented way to do it, not tightening the style further.

## related
- [[skills/token-thrift/SKILL|token-thrift]] — the practical side of the same question: fewer calls and less context per call are the only two levers, measured rather than assumed
- [[2026-08-28 agent instruction bloat - modular skills and compact synthesis]] — the same "classify what's essential, cut the rest" idea already applied to one growing markdown file vs. discrete skill modules, with measured token-overhead numbers
- [[header extraction for token-efficient retrieval]] — a concrete worked example of the "agent-read-only notes" case above: measured 77.5% token reduction extracting headers instead of full note bodies
- [[token efficient PKM analysis architecture]] — token budgets across agent operations more broadly
