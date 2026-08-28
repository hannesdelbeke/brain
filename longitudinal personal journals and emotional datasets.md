---
date: 2026-08-27
created: 2026-08-27
tags:
  - ai
  - datasets
  - psychology
  - journaling
  - pkm
  - longitudinal
aliases:
  - 2026-08-27 longitudinal personal journals and emotional datasets
  - longitudinal personal journals
  - single author lifelogs and diary datasets
  - public personal journals
---

# Longitudinal Personal Journals & Single-Author Emotional Datasets

An index of sources where **one person records their inner life over months, years or decades**: web journals, public-domain diary corpora, and published diaries in book form.

Inclusion rule: the source has to be the journal itself, written by one identifiable person, tracking emotional state over time. Software for publishing notes, tooling repos, and multi-author sentiment benchmarks are out of scope — see [Excluded](#excluded-and-why) at the bottom.

Every link below was checked and returns the described page (last checked 2026-08-27).

---

## Web journals by one author

### Aaron Swartz — Raw Thought (2002–2012)
* **URL:** [aaronsw.com/weblog](http://www.aaronsw.com/weblog/) · [full archive index](http://www.aaronsw.com/weblog/archive)
* **Span:** 10 years, closed corpus — the author died in 2013, so the arc is complete rather than ongoing.
* **Why it fits:** public writing about depression, illness, shame and motivation alongside the technical posts, with dates on everything.
* **Entries:**
  * [Sick](http://www.aaronsw.com/weblog/verysick) — first-person account of depression as a physical illness.
  * [Life in the Hospital](http://www.aaronsw.com/weblog/hospitallife) and [Alone in the Hospital](http://www.aaronsw.com/weblog/hospitalbabies) — 2007 hospitalisation.
  * [The Book That Changed My Life](http://www.aaronsw.com/weblog/epiphany) — belief revision, named and dated.

### Nick Cave — The Red Hand Files (2018–present)
* **URL:** [theredhandfiles.com](https://www.theredhandfiles.com/)
* **Span:** 7+ years, numbered issues, no moderator between question and answer.
* **Why it fits:** sustained public working-through of the death of his son. Grief tracked issue by issue rather than in one retrospective.
* **Shape of the data:** reader question + long personal reply, every issue numbered and dated.

### Derek Sivers — sive.rs (1998–present)
* **URL:** [sive.rs](https://sive.rs)
* **Span:** 25+ years.
* **Entries:**
  * [Why I gave away my company](https://sive.rs/trust) — aftermath of betrayal and of giving away the proceeds of CD Baby.
  * [There's no speed limit](https://sive.rs/kimo) — mentorship and self-imposed limits.
  * [Avoid drama](https://sive.rs/drama) — boundary setting.
  * [Book notes](https://sive.rs/book) — 300+ books with personal reactions and ratings, dated, 20 years deep.

### Buster Benson — Codex Vitae (2010–present)
* **URL:** [github.com/busterbenson/public](https://github.com/busterbenson/public) · [busterbenson.com](https://busterbenson.com/)
* **Entries:**
  * [book-of-beliefs.md](https://github.com/busterbenson/public/blob/master/book-of-beliefs.md) — his beliefs as a git-versioned file. The **git history is the dataset**: every revision is a dated belief change with a diff.
* **Why it fits:** the only source here where belief drift is machine-readable by construction.
* Note: earlier drafts of this note linked `busterbenson.com/beliefs/` and `/praise/`. Both 404. Use the repo.

### Gwern Branwen — gwern.net (2009–present)
* **URL:** [gwern.net](https://gwern.net)
* **Why it fits:** quantified rather than narrative. Mood as numbers, self-blinded.
* **Entries:**
  * [Zeo sleep experiments](https://gwern.net/zeo) — years of daily sleep and subjective mood, [downloadable data](https://gwern.net/zeo#data).
  * [Melatonin](https://gwern.net/melatonin) — blinded self-trials with mood outcomes.
  * [Calibration](https://gwern.net/calibration) — tracked confidence against outcomes over time.

### Jacky Zhao — jzhao.xyz (2019–present)
* **URL:** [jzhao.xyz](https://jzhao.xyz)
* **Entries:** [burnout](https://jzhao.xyz/thoughts/burnout), [pain](https://jzhao.xyz/thoughts/pain), [self-confidence](https://jzhao.xyz/thoughts/self-confidence), [agency](https://jzhao.xyz/thoughts/agency), [dappled light](https://jzhao.xyz/posts/dappled-light).
* Note: the notes are undated on the page, which limits them for time-series work. Earlier drafts linked `/thoughts/loneliness` and `/posts/reflecting-on-2023`; both 404.

### David Cain — Raptitude (2009–present)
* **URL:** [raptitude.com](https://www.raptitude.com/)
* **Span:** 16 years of dated first-person essays on mood, avoidance, habit and attention, written by one person about their own experience.

---

## Public-domain diary corpora (full text, downloadable)

These are the ones worth pointing a pipeline at: complete, dated, day-by-day, no licence problem.

### Samuel Pepys, 1660–1669
* **Text:** [Project Gutenberg — The Diary of Samuel Pepys, Complete](https://www.gutenberg.org/ebooks/4200)
* **Browsable:** [pepysdiary.com](https://www.pepysdiary.com/) — one entry per day with annotations.
* **Entries:** [15 June 1665, plague](https://www.pepysdiary.com/diary/1665/06/15/) · [2 September 1666, Great Fire](https://www.pepysdiary.com/diary/1666/09/02/) · [25 October 1668, marriage crisis](https://www.pepysdiary.com/diary/1668/10/25/)
* 10 consecutive years, written without an audience in mind, in shorthand.

### Marcus Aurelius, *Meditations*, c. 170–180 AD
* **Text:** [Project Gutenberg 2680](https://www.gutenberg.org/ebooks/2680)
* Private notes to self. No dates and no chronology, so it reads as emotional regulation technique rather than as a time series.

### Leo Tolstoy, diaries
* **1895–1899:** [Project Gutenberg 46272 — The Journal of Leo Tolstoi, First Volume](https://www.gutenberg.org/ebooks/46272)
* **1847–1852:** [archive.org — The Diaries of Leo Tolstoy (Hogarth trans., 1917)](https://archive.org/details/diariesofleotols00tols)
* Tolstoy kept diaries from 18 to his death at 82. Only fragments of that are in public-domain English translation — the two above, not the full 63 years.

### Henry David Thoreau, Journal 1837–1861
* **Text:** [The Walden Woods Project — The Journal of Henry David Thoreau](https://www.walden.org/collection/journals/)
* 24 years, near-daily, ~2 million words. Long enough for seasonal and multi-year mood structure.

### George Orwell, diaries 1938–1942
* **URL:** [orwelldiaries.wordpress.com](https://orwelldiaries.wordpress.com/) — republished one entry per day, 70 years to the day after writing. Example: [28 June 1940](https://orwelldiaries.wordpress.com/2010/06/28/28-6-40/).
* Domestic and war diaries mixed; emotionally flat by design, useful as a contrast case.

### Virginia Woolf, *A Writer's Diary* (1918–1941)
* **Scan:** [archive.org — A Writer's Diary](https://archive.org/details/in.ernet.dli.2015.509772)
* 23 years of the creative cycle: elation, dread of reviews, depressive collapse, the Blitz, ending weeks before her suicide.

### Franz Kafka, diaries 1910–1923
* **Scan (borrow only, not downloadable):** [archive.org — The Diaries of Franz Kafka 1910–1913](https://archive.org/details/diariesoffranzka0000maxb_c9u3); the 1914–1923 volume is catalogued separately.
* The `the-diaries-of-franz-kafka-1910-1923` identifier used in an earlier draft does not exist.

---

## Book-length single-person journals

Not free, not machine-readable, listed because each one is a sustained emotional record by one person and several have no online equivalent.

* **Marion Milner, *A Life of One's Own* (1934)** — seven years of diary kept as an experiment to find out what actually made her happy. The closest thing in print to a deliberately designed single-subject emotional dataset. See [[Marion Milner - A Life of One's Own|A Life of One's Own summary]].
* **May Sarton, *Journal of a Solitude* (1973)** — one year, solitude, depression, aging, written against her own earlier idealised account of the same life.
* **Sylvia Plath, *The Unabridged Journals* (1950–1962)** — 12 years, ends shortly before her death.
* **Etty Hillesum, *An Interrupted Life* (1941–1943)** — diaries and letters, Amsterdam through deportation.
* **Anne Frank, *The Diary of a Young Girl* (1942–1944)** — two years, adolescent emotional development under confinement. Still in copyright in most territories.
* **C.S. Lewis, *A Grief Observed* (1961)** — four notebooks kept during bereavement; short, and the closest thing to a raw grief log.
* **John Steinbeck, *Journal of a Novel* (1951)** — a daily entry written before each day's work on *East of Eden*: self-doubt tracked against measurable output.
* **Sarah Manguso, *Ongoingness* (2015)** — about keeping a 25-year, 800,000-word diary; a source on the practice, not the diary itself.

---

## Excluded, and why

Removed from earlier versions of this note:

* **jackyzha0/quartz** — static site generator. Software, not a journal. The journal is [jzhao.xyz](https://jzhao.xyz), kept above.
* **jethrokuan/braindump** — technical study notes (algorithms, Emacs, ML). No emotional content.
* **philgyford/pepysdiary** — the Django code that runs pepysdiary.com. The text is Gutenberg 4200, linked above.
* **Hallucinated links**, verified dead: `jzhao.xyz/thoughts/loneliness`, `jzhao.xyz/posts/reflecting-on-2023`, `busterbenson.com/beliefs/`, `busterbenson.com/praise/`, `archive.org/details/the-diaries-of-franz-kafka-1910-1923`. Two Gutenberg/archive IDs pointed at unrelated books: `gutenberg.org/ebooks/24816` is *Life at Puget Sound*, not Tolstoy; `archive.org/details/in.ernet.dli.2015.499153` is *Colour and Colour Theories*, not Woolf.

Also out of scope: multi-author corpora (Blog Authorship Corpus, Mass Observation, scraped Reddit), and quantified-self projects with no emotional variable (Feltron annual reports, step and sleep exports).

---

## AI Analysis Framework: Tracking Emotional Evolution

When analysing one of these corpora with an LLM agent, run the extraction across chronological slices (quarterly or yearly):

```
┌───────────────────────────────────────────────────────────┐
│              LONGITUDINAL EXTRACTION PIPELINE             │
├───────────────────────────────────────────────────────────┤
│ 1. Emotional Baseline:                                    │
│    Identify the dominant emotional state (e.g., anxiety,  │
│    striving, grief, flow, contentment).                   │
│                                                           │
│ 2. Crisis & Pivot Identification:                         │
│    What acute failure or crisis forced a change in        │
│    belief or behavior?                                    │
│                                                           │
│ 3. Reframing Half-Life:                                   │
│    How long did it take the author to reframe the event?  │
│    (Compare emotional tone at +1 week, +3 months, +2 yrs).│
│                                                           │
│ 4. Locus of Control Shift:                                │
│    Did attribution move from external blame to internal   │
│    agency and radical acceptance?                         │
│                                                           │
│ 5. Belief Stability & Drift:                              │
│    Which core values remained constant vs. inverted?      │
└───────────────────────────────────────────────────────────┘
```

Corpora that support this directly, in order of how little cleanup they need: Pepys (dated, complete, plain text), Thoreau (dated, complete), Gwern's Zeo data (numeric), Buster Benson's git history (diffs are the signal), Aaron Swartz (dated, complete, closed).

---

## 🔗 Related Notes
- [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]] — how longitudinal episodic memory and living user profiles enable genuine AI thought partnership
- [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]] — memory reconsolidation, emotional amygdala weighting, and sleep consolidation
- [[public/skills/private-to-public-note-promotion/SKILL|private to public note promotion]] — safety rules and procedures for public note releases
