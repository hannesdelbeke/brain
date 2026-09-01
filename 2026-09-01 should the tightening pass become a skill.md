> [!summary] eli5
> a human editing pass on a paper's plain-language summary cut much harder than this session's own drafts did — whole clarifying sentences gone, not just filler words. asked whether that editing standard should apply to all vault notes, or become a skill.
> done. recommendation: no blanket application, no new skill from scratch. scope it to outward-facing hook text only (paper abstracts, plain-language summaries, blog intros), and if built as a skill, gate it the same way [[skills/note-compress/SKILL|note-compress]] already gates compression — classify signal vs. filler, cut only filler — not a raw word-count minimizer.
> **needs from you:** nothing, this is the answer to the question asked; a skill would need real usage across several summaries before it's worth generalizing into scripted form.

> the tightening pass, would it be worth applying to all my notes, or also turn into a skill

**why:** [[talent density, information density, and why shorter isn't automatically denser]]

## the example this recommendation is built on

the actual edit, from a paper draft's plain-language summary (see the private publish-plan note for the full draft — the edit itself has no vault-b-specific data, reproduced here):

**before (this session's draft):**
> imagine asking an AI assistant to find the note, file, or past decision that's actually relevant to what you're working on right now, out of thousands of candidates. one shortcut worth testing: things made around the same *time as each other* tend to be related — not "recent" in the sense of freshly made, but close together on the calendar, whenever that was. two notes written the same afternoon three years ago count just as much under this idea as two things made an hour apart today. that shortcut is not free — build it into a ranking system the wrong way, and it actively makes results worse, not just unhelpful.

**after (the human's edit):**
> imagine asking an AI assistant to find a note, file, or past decision relevant to what you're working on right now, out of thousands of candidates.
> Things made around the same *time as each other* tend to be related, but build it into a ranking system the wrong way, and it actively makes results worse.

three different cuts happened here, and they don't all carry the same risk:

- **"that's actually" → "relevant"** — pure filler, zero information lost. always a good cut, anywhere.
- **"one shortcut worth testing:"** — a lead-in phrase, telegraphing structure the sentence doesn't need. safe to cut in a hook; would matter more in a formal methods section where signaling "this is a hypothesis, not a finding" is load-bearing.
- **the entire "not recent... three years ago" sentence** — this is the risky one. it's not filler, it's the one sentence that made the distinction between *time-proximity* and *absolute recency* concrete. cutting it doesn't just shorten the paragraph, it removes the only place that distinction gets explained in plain language.

that third cut is exactly the failure mode [[2026-08-31 classifier-based compression with an adversarial fidelity gate|this vault's own compression research]] already measured and named: a classifier-style compressor that can remove whole clauses saves more words than a rule-based one, and its own failure mode is losing hedges, causal connectors, and — the closest match here — the connective texture that carries a distinction the rest of the text now assumes the reader already has.

## why it's still the right cut, here

the missing distinction doesn't disappear from the paper — it's restated in the technical abstract two sections down, in more precise language, for the reader who's still reading by then. a plain-language summary's job is to get a stranger to keep reading, not to be the only place a claim is fully specified. cutting the example trades a small amount of precision, recoverable later in the document, for a faster hook. that's a legitimate trade for this document type. it would not be a legitimate trade in a reference note meant to stand alone, where there's no "further down" to recover the cut information from.

## the recommendation

**scope: front-matter and hooks only** — paper abstracts, plain-language summaries, blog intros, chat replies (caveman mode already does exactly this for chat output, and already exempts persisted documents from it — the same boundary this recommendation draws, arrived at independently). **not**: this vault's own reference notes, technical sections, anything meant to be read once and trusted as complete, per this vault's own convention that "a note whose state cannot be worked out from its own text was never finished."

**don't build a new skill from a single edit.** one data point isn't enough to script a reusable rule from — the next few times this kind of tightening happens, by hand, are what would reveal whether there's a stable, generalizable pattern (which sentence types are safe to cut, which aren't) or whether it's a case-by-case judgment call that resists automation. revisit this after a handful more real examples exist.

**if it does get built later**, the shape is already proven in this vault: classify each sentence as signal or filler (the same operation [[2026-08-31 classifier-based compression with an adversarial fidelity gate|the classifier-based compression method]] already does), cut only filler by default, and treat "cut a signal-bearing sentence" as an explicit, opt-in, hook-only override rather than the default behavior — with a check afterward for whether a fact, hedge, or the only explanation of a distinction got lost, the same fidelity-gate shape [[skills/note-compress/SKILL|note-compress]] already runs for agent-facing notes, adapted to ask "does a human reader lose something they can't get back later" instead of "did a link or number survive."

## related

- [[talent density, information density, and why shorter isn't automatically denser]] — the general framework this recommendation applies
- [[2026-08-31 classifier-based compression with an adversarial fidelity gate]] — the existing mechanism this recommendation reuses the shape of
- [[2026-08-30 agent reading versus human reading, which formatting rules transfer]] — the same "depends on the reader" shape, for formatting instead of density
