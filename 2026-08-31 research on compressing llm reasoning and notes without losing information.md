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

## caveman-compress benchmarked against the vault's own method, on the same notes

a private compression experiment ran the llmlingua-2-style idea above for real: an agent classified tokens as essential (facts, numbers, decisions, links) versus disposable (connective prose), cut only the disposable, and a second, adversarial agent scored the result against the original for lost meaning. five real notes went through it — two short pre-distilled claim notes, two narrative technical write-ups, and one long dense reference note.

| note type | words before → after | cut | retention (adversarial, /100) |
| :--- | :--- | :--- | :--- |
| claim note A | 116 → 70 | 40% | 90 |
| claim note B | 108 → 74 | 31% | 88 |
| narrative A | 554 → 347 | 37% | 85 |
| narrative B | 844 → 546 | 35% | 89 |
| dense reference | 1,711 → 1,187 | 31% | 98 |

nothing lost touched a number, code identifier, or link across all five. what broke: epistemic markers ("observed" dropped, turning a confirmed finding into an unmarked claim), confidence hedges flattened into stronger claims than the original made, and causal/provenance framing. the dense reference note, mostly facts and links with light connective prose, scored highest (98) — the case closest to what a token classifier is built for. the two narrative notes, carrying a chain of reasoning rather than a table of facts, scored lowest (85, 89) — reasoning is what a prompt-based compressor eats first.

**caveman-compress run on the identical five notes**, real skill, real tokens (`tiktoken`, `cl100k_base`):

| note type | tokens before → after | cut (caveman) | cut (vault's classifier method) | retention (adversarial, /100) |
| :--- | :--- | :--- | :--- | :--- |
| claim note A | 179 → 155 | 13.4% | 40% | 85 |
| claim note B | 156 → 137 | 12.2% | 31% | 88 |
| narrative A | 816 → 703 | 13.8% | 37% | 92 |
| narrative B | 1,012 → 824 | 18.6% | 35% | 93 |
| dense reference | 2,626 → 2,327 | 11.4% | 31% | 96 |

**compression: caveman-compress saves 11-19%, the classifier method saves 31-40%, on the identical notes** — under half, every time, with the widest relative gap on the dense reference note (11.4% vs. 31%), exactly the case the classifier method captured best and a fixed word-level rule list structurally cannot.

**fidelity: statistically the same band** (caveman-compress 85-96, avg 90.8; classifier method 85-98, avg ~90) — not safer, not more careless, just failing a different way. every number, code identifier, and link held exact across all five files, matching caveman-compress's own "preserve exactly" rule. what it drops instead: causal connectives. `"restated per agent because a fresh one inherits none of it"` becomes `"restated per agent, fresh agent inherit none"` — the causal link becomes juxtaposition, the reader now infers why instead of being told. `"saves 3.4% at some cost in quality"` becomes `"saves 3.4% at cost in quality"` — the hedge ("some," small and uncertain) is gone, reading as a flatter, more definite cost than the original stated. this is the predicted failure mode of a fixed word-drop list: it cannot tell a load-bearing "because" or "some" from a disposable one, so it treats every instance of a droppable-word-class the same regardless of what that specific instance is carrying.

## why caveman-compress lands where it does

caveman-compress operates at the word/phrase level (drop articles, filler, hedging phrases) with a hard rule to preserve every heading, bullet, and list item's structure — so it can never remove a whole disposable clause or sentence the way the classifier method does, and it never gets to exploit a dense, mostly-factual passage the way the classifier method's 98-retention win on the reference note did. that ceiling is structural, not a tuning gap: raising its aggressiveness would mean cutting into the same word classes (hedges, causal connectives) that are already where its fidelity loss concentrates, trading more compression for the exact same failure mode at higher volume, not a new one.

**the live caveman chat-mode has a different, narrower scope than either of these.** it compresses what the assistant writes in conversation, not vault notes — persisted content (docs, code, commits, memory files) is explicitly exempt from the base mode; only the separate caveman-compress skill above touches files, and only on request. it also has no adversarial fidelity gate of its own: its measured numbers are token counts, not retention scores, and its own design carves out security warnings, irreversible-action confirmations, and multi-step sequences as places it must drop back to normal prose — a tacit acknowledgment that the compression itself can create dangerous ambiguity outside those carve-outs. and it shares the reasoning-length ceiling from the section above: a fixed intensity level doesn't know a harder task's token-complexity floor, so a level that's safe on one task can start cutting real content on another.

the practical read for a vault compression skill: caveman-compress's mechanical rules are a real, small, safe-ish win (roughly 12-19%, same fidelity band as a much stronger method) with no judgment calls to get wrong — but they leave most of the token budget on the table precisely where a note is dense and factual, the case a smarter method wins hardest. the vault's own study reaches the same conclusion the caveman-compress rule set arrives at structurally: don't run either one unattended without a fidelity check, since a compressor — rule-based or learned — cannot be trusted to know which of its own cuts removed an argument rather than a word.

## related
- [[skills/token-thrift/SKILL|token-thrift]] — the practical side of the same question: fewer calls and less context per call are the only two levers, measured rather than assumed
- [[2026-08-28 agent instruction bloat - modular skills and compact synthesis]] — the same "classify what's essential, cut the rest" idea already applied to one growing markdown file vs. discrete skill modules, with measured token-overhead numbers
- [[header extraction for token-efficient retrieval]] — a concrete worked example of the "agent-read-only notes" case above: measured 77.5% token reduction extracting headers instead of full note bodies
- [[token efficient PKM analysis architecture]] — token budgets across agent operations more broadly
