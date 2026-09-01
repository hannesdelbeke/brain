---
date: 2026-08-30
created: 2026-08-30
tags:
  - pkm
  - readability
  - ux
  - cognitive-science
  - writing
---

# 👁️ Readability and Reading-Speed Research, Applied to a Note Vault

Most "read faster" tricks (Bionic Reading, RSVP speed-reading apps) fail controlled studies. What actually moves the needle is structure that lets a reader **scan instead of read**: bolded lead words, short chunks, a conclusion up front. This note collects the research and turns it into concrete note-writing rules.

Related: [[2026-08-29 stub vs hub - heuristic for link-only note value|stub vs hub]]

---

## What doesn't work

**Bionic Reading** (bolding the first few letters of each word) has no controlled-study support for the general population. A 2,000+ participant test found readers 2.6 wpm *slower* with it, comprehension unchanged or slightly worse ([Readwise](https://blog.readwise.io/bionic-reading-results/)); a 2024 peer-reviewed study is titled outright "[No, Bionic Reading does not work](https://www.sciencedirect.com/science/article/pii/S0001691824001811)". The mechanism: about 35% of words are never fixated during normal reading, and bolding makes every word salient, which removes the skippability that made reading fast in the first place. It may still help specific populations — dyslexia, ADHD, visual tracking issues — but the evidence there is thin and the general-reader result is a clear null.

**RSVP speed-reading** (Spritz and similar, flashing one word at a time) is debunked by the definitive review, [Rayner et al. 2016, "So Much to Read, So Little Time"](https://journals.sagepub.com/doi/10.1177/1529100615623267). RSVP removes the reader's ability to make backward eye movements ("regressions"), and most regressions exist to repair a comprehension failure — so RSVP readers keep moving forward while holding a wrong interpretation. The peripheral-vision claim behind some speed-reading courses ("read a whole page at once") isn't biologically possible either; word-identification accuracy collapses a few degrees outside the fixation point. Speed and comprehension trade off directly: push speed well past normal, comprehension drops, no exceptions found.

**Takeaway for a vault:** don't add bolding-every-word or RSVP-style tooling. The reader isn't reading slower because word recognition is the bottleneck, they're reading slower because they have to read the whole thing to find what's relevant. Structure solves that; typographic tricks on the character level don't.

## What actually works

**People scan, they don't read.** Nielsen and Morkes' original study found 79% of users scan a new page rather than read word for word ([NN/g](https://www.nngroup.com/articles/how-users-read-on-the-web/)). Combining three writing changes — concise text, scannable formatting, plain language — measured **124% better usability** than a baseline in Nielsen's controlled test. That's the largest effect size in this whole research area, and it comes from prose structure, not typography.

**The F-pattern.** Eyetracking across three studies and 500+ participants shows people read the first line fully, then scan down the left edge, reading only the first word or two of each following line before deciding whether to keep going ([NN/g](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content-discovered/)). The direct consequence: **put the information-carrying word first** in a heading, bullet, or paragraph. A reader scanning your left margin decides whether to keep reading based on word one and two, not word ten.

**Signaling / cueing (Mayer's Cognitive Theory of Multimedia Learning).** Bolding or highlighting the essential words in a block of text measurably improves a reader's ability to find and retain the cued information, by directing attention before the reader has to search for it themselves ([overview](https://www.digitallearninginstitute.com/blog/mayers-principles-multimedia-learning)). The caveat every source repeats: **it only works if used sparingly**. Bold everything and nothing stands out, which is the same failure mode as Bionic Reading at paragraph scale instead of word scale.

**Inverted pyramid.** Put the conclusion first, detail after. Nielsen's tests found this alone produced better task performance, not just user preference, and think-aloud participants explicitly praised getting the point "right away" ([NN/g](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/)). This is the same shape as an abstract, a tl;dr, or an eli5 callout at the top of a note — a reader who stops after the first two lines still walks away with the actual answer.

**Line length.** 50–75 characters per line is the converging recommendation across typography research; the most-cited screen study found 55 characters preferred and easiest to read, though raw reading *speed* actually increases with somewhat longer lines — speed and preference point in slightly different directions ([UXPin](https://www.uxpin.com/studio/blog/optimal-line-length-for-readability/), [Dyson & Kipping via Human Factors](https://www.humanfactors.com/newsletters/optimal_line_length.asp)). Practical read: don't hard-wrap markdown at a fixed column, let the editor soft-wrap at something in this range, avoid both very long unbroken paragraphs and very narrow columns.

**Chunk to working-memory limits.** Miller's classic "seven plus or minus two" ([1956](https://labs.la.utexas.edu/gilden/files/2016/04/MagicNumberSeven-Miller1956.pdf)) was already a rough estimate; Cowan's 2001 reanalysis, controlling for rehearsal, put real working-memory capacity closer to **four chunks** ([overview](https://en.wikipedia.org/wiki/The_Magical_Number_Seven,_Plus_or_Minus_Two)). A bulleted list a reader is meant to actually hold in mind — not just scan and file away — should be sized closer to four or five items than ten or fifteen. Past that, group into sub-headings, the reader re-chunks by heading instead of by item and the limit resets.

**Meaningful link text.** Nielsen's eyetracking again: readers fixate on the first couple of words of a link when scanning a list of links, so front-load the link text with the actual subject, and never use "click here" or "learn more," which carry zero information scent on their own ([NN/g](https://www.nngroup.com/articles/writing-links/)). This generalizes directly to wikilinks: `[[2026-08-17 network segmentation for a smart-home device]]` scans, the subject is right there in the link text; a bare `[[link]]` or `[[click here]]` doesn't.

## Applied to a note vault

Put together, the findings converge on one instruction: **write so the first two words of every line carry the meaning**, and use the rest of these to support that.

- **lede first, detail after** — an eli5/tl;dr line at the top of a note is the inverted pyramid; a reader who reads only that line still gets the actual conclusion, not just the topic
- **bold the subject, not the sentence** — a short bold lead-in per bullet (`**topic:** the rest of the sentence...`) is the signaling principle applied at list-item scale; bolding the whole bullet or whole paragraph defeats it, the cue needs contrast to work
- **front-load headings and bullets** — the F-pattern means word one and two decide whether the rest gets read; lead with the noun, not "so," "regarding," or a citation
- **cap list length near four or five, not ten** — a queue of more than about five items a reader is meant to actually weigh (not just skim past) should split under sub-headings by category, so the reader re-chunks per heading instead of holding the whole list at once
- **name the destination in every link** — `[[2026-08-30 what a commit history reveals about a recurring mistake]]` scans as a subject; `[[here]]` or `[[this note]]` doesn't, and costs the same click either way
- **let lines soft-wrap, don't hard-wrap at a fixed width** — 50–75 characters is the readable range, but that's an editor/display setting, not something to bake into the markdown source with manual line breaks
- **skip bolding-every-word or auto-highlighting tools** — Bionic Reading and RSVP are the two most heavily marketed "read faster" interventions and both fail controlled tests for general readers; the actual lever is note structure, not a rendering trick applied on top of unstructured prose

None of this trades off comprehension for speed the way RSVP or literal speed-reading does — every technique above is about **retrieval**, getting a reader to the relevant sentence faster, not about pushing raw words-per-minute on the sentence itself once they're there. That's also why it composes with existing note conventions like a tl;dr callout or a distilled-claims layer over raw logs: those are inverted-pyramid and chunking applied at the note and vault level instead of the sentence and list level.
