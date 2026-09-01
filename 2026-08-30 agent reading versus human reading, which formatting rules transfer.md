---
date: 2026-08-30
created: 2026-08-30
tags:
  - readability
  - llm
  - ux
  - cognitive-science
  - pkm
---

# 🤖👁️ Agent Reading vs. Human Reading: Which Formatting Rules Transfer

The formatting rules in [[2026-08-30 readability and reading-speed research applied to note-taking vaults|the readability research note]] all come from human perception and memory research — a fovea, a working-memory register, eye saccades. An LLM reading a prompt or a note has none of those. Some rules turn out to transfer anyway, for a different mechanism; others don't transfer at all and just cost tokens for no benefit.

Related: [[2026-08-30 readability and reading-speed research applied to note-taking vaults|readability and reading-speed research]]

---

## Why the mechanisms don't match

A human reader scanning a page uses **saccades**, fast eye jumps between fixation points, with sharp vision only in a small foveal window. That's the physical basis of the F-pattern: people only clearly see the first word or two of a line before deciding whether to fixate further right or drop down. A human's working memory then holds roughly four chunks of what was read ([Cowan 2001](https://en.wikipedia.org/wiki/The_Magical_Number_Seven,_Plus_or_Minus_Two), verified 2026-09-01) before it needs re-chunking.

An LLM has no eyes and no working-memory register in that sense. A transformer processes an entire input through self-attention in effectively one pass; there's no foveal window, no saccade, no chunk limit in the human sense. Whatever governs an LLM's use of a long input is a different mechanism entirely — attention weighting and positional encoding, not vision and short-term memory.

## What still transfers, and why

**Headers.** A formatting study across OpenAI's GPT family ([arXiv:2411.10541](https://arxiv.org/html/2411.10541v1), verified 2026-09-01) found prompt format changes performance by up to 40% on some tasks for smaller/older models, with headers consistently the most useful single element — they work like labeled sections a model can key off when deciding which part of the input answers which part of the task. This is functionally similar to why headers help a human scanner (they signal structure before content), even though the underlying mechanism, task-structure parsing versus perceptual layer-cake scanning, is different. Frontier-scale models are more robust to formatting overall, but headers still cost almost nothing and never hurt.

**Lede-first / conclusion-first.** ["Lost in the Middle"](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf) (Liu et al. 2023, arXiv:2307.03172, verified 2026-09-01) found a U-shaped performance curve in long-context LLMs: information at the very start or very end of the input gets used well, information buried in the middle gets used badly, sometimes worse than if it weren't provided at all. That's not the F-pattern, it's a consequence of how causal attention and positional encoding weight earlier and later tokens. But it recommends the identical instruction as the human-side inverted-pyramid research: put the important thing first (or repeat it at the end), don't bury it in the middle of a long block.

**Plain, concise language.** Halving word count and cutting filler helps a human scanner because there's less to scan past to find the point. It helps an LLM reader for an unrelated reason: fewer tokens means the actual signal is a larger fraction of a fixed context budget, and cost/latency scale with tokens either way. Two different justifications, same instruction.

## What doesn't transfer

**Bold and other emphasis markup.** The signaling principle (Mayer) works on a human by pre-attentively guiding eye movement toward cued words before reading starts — it's a perceptual shortcut. An LLM doesn't have eye movement to guide. The same formatting research above describes bold/emphasis effects on LLMs as weak and contested, "not a substitute for the clear, structural guidance that headings and lists provide." Bolding a block of agent-facing text is close to free in tokens, but there's no solid evidence it does anything, unlike headers.

**Chunk-size limits.** Capping a list at four or five items exists because that's roughly what a human can hold in working memory before needing to re-chunk by heading. An LLM reading a list of twelve isn't holding it in a working-memory slot between reads, it has the whole list in context at once. Splitting an agent-facing list to respect a four-item human limit doesn't reduce any burden the model actually has, it just adds header tokens.

**Line length and typography.** 50–75 characters per line is about saccade length and physical eye strain on a display. It has no analogue for a model reading tokens rather than rendered pixels. This one is purely a display-layer concern, relevant only to whatever renders the text for a human afterward, not to the model consuming it directly.

## Practical split

| Technique | Human-facing text | Agent-facing text (prompts, memory bodies, inter-agent messages) |
|---|---|---|
| Headers / sections | keep | keep — cheap, evidence supports it here too |
| Lede-first / conclusion up front | keep | keep — different mechanism, same payoff |
| Plain, concise language | keep | keep — token cost applies equally |
| Bold subject per bullet | keep | drop — weak/contested LLM effect, costs tokens |
| Four-or-five-item chunk cap | keep | drop — no working-memory limit to respect |
| Optimal line length / typography | keep (rendered display) | not applicable — no visual rendering in play |

The practical rule: formatting justified by *information architecture* (what's structurally where, what's said first) tends to transfer, because both a human and a model are extracting structure and priority from the same text. Formatting justified by *perception or short-term memory* (visual salience, saccades, chunk limits) doesn't transfer, because those constraints are specific to having a body and a fovea.

## an unrelated field already answered this exact question

accessibility research for screen-reader users has the identical split, formalized decades before LLMs existed: [WCAG 1.3.1 "Info and Relationships"](https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html) (verified 2026-09-01) requires that information conveyed through visual presentation have a programmatic equivalent, or it fails accessibility outright. A screen-reader user has no fovea and no saccades either — a different "body," same underlying question this note asks about an LLM reader. The field's own answer matches this note's split exactly: semantic heading structure transfers (the [WebAIM Screen Reader User Survey](https://webaim.org/projects/screenreadersurvey10/) (verified 2026-09-01) found 71.6% of screen-reader users navigate by jumping between headings, only 6.4% read linearly — headings are load-bearing information architecture, not decoration), while bold/italic markup is "not reliably announced" by many screen readers and color-only meaning fails WCAG outright — both perceptual-channel artifacts with no non-visual equivalent, the same conclusion this note reaches about bold for an LLM, for a structurally identical reason. Worth citing directly: a mature, already-validated framework for "which conventions survive a change in reader apparatus" existed all along, just never applied to an LLM reader before.

Braille transcription (BANA's *Braille Formats 2016*, not independently checked, search budget ran out this pass) sits at an interesting middle point: font attributes (bold/italic) don't transfer and get replaced with a transcriber's note rather than faked, but the *function* some visual conventions serve (knowing where you are in a document) gets reinvented in braille's own vocabulary rather than dropped — a reminder that "doesn't transfer literally" and "the underlying need disappears" aren't always the same thing.
