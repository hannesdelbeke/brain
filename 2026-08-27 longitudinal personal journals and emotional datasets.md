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

A curated index of **public, single-person personal journals, digital gardens, and historical daily diary corpora** spanning months, years, or decades. 

Unlike generic multi-author NLP sentiment benchmarks (e.g. Kaggle surveys or scraped Reddit comments), these datasets track a **single human mind over time**—allowing researchers and AI models to study authentic emotional arcs, belief revisions, cognitive reframing, and psychological resilience.

---

## 🌿 Modern Single-Author Open Repositories (5–15+ Years)

### 1. [nikitavoloboev/my-life](https://github.com/nikitavoloboev/my-life) & [nikitavoloboev/knowledge](https://github.com/nikitavoloboev/knowledge)
* **Author:** Nikita Voloboev
* **Timespan:** ~2016 – Present (8+ years)
* **Format:** Markdown repository / Git-versioned personal wiki
* **Emotional & Psychological Core:** One of the most transparent, raw personal life-logging repositories on GitHub.
  * **Mental Health & Therapy:** Unfiltered documentation of burnout, therapy sessions, AuDHD traits, chronic fatigue, and existential anxiety.
  * **Belief Evolution:** Year-over-year habit reviews, relationship shifts, career transitions, and radical reassessments of life philosophy.
  * **Granularity:** Spans thousands of atomic markdown files tracking daily habits, tools, emotional highs, and depressive episodes.

### 2. [gwern/gwern.net](https://github.com/gwern/gwern.net)
* **Author:** Gwern Branwen
* **Timespan:** 2009 – Present (15+ years)
* **Format:** Git-versioned Hakyll/Markdown site source
* **Emotional & Psychological Core:** Rigorous quantified-self and long-term epistemic tracking.
  * **Blind Mood Self-Experiments:** 10+ years of daily mood scoring correlated against sleep, light therapy, nootropics, and life events.
  * **Personal Grief & Eulogies:** Deeply personal writing on mortality, loss, and the emotional cost of long-term isolation.
  * **Epistemic Calibration:** Explicit historical tracking of percentage confidence intervals on personal and philosophical beliefs over decades.

### 3. [Jacky Zhao's Digital Garden](https://github.com/jackyzha0) ([jzhao.xyz](https://jzhao.xyz))
* **Author:** Jacky Zhao (creator of Quartz)
* **Timespan:** 2019 – Present (5+ years)
* **Format:** Markdown / Quartz digital garden
* **Emotional & Psychological Core:** Longitudinal coming-of-age trajectory of a young technologist.
  * **Burnout & Creative Exhaustion:** Essays on the emotional weight of university transitions, open-source pressure, and creative identity.
  * **Vulnerability & Community:** Evolving philosophies on human connection, intentional community living, and moving away from shallow ambition.

### 4. [jethrokuan/braindump](https://github.com/jethrokuan/braindump)
* **Author:** Jethro Kuan
* **Timespan:** 2018 – Present (6+ years)
* **Format:** 1,000+ interconnected `org-mode` / Markdown notes
* **Emotional & Psychological Core:** Psychological arc through undergraduate education into PhD research.
  * Captures the internal friction of academic imposter syndrome, research anxiety, mental health maintenance, and cognitive habits.

### 5. [Derek Sivers Life Archive](https://github.com/sivers) ([sive.rs](https://sive.rs))
* **Author:** Derek Sivers (founder of CD Baby)
* **Timespan:** 1998 – Present (25+ years)
* **Format:** Plaintext / static website repository
* **Emotional & Psychological Core:** Two decades of high-stakes life decisions and emotional reckonings.
  * Reflections on selling and giving away CD Baby ($22M trust), navigating divorce, solo travel, fatherhood, and minimalism.
  * 300+ book summaries paired with personal emotional reactions and life directives.

### 6. [Buster Benson (15-Year Life Question Logs)](https://busterbenson.com)
* **Author:** Buster Benson (creator of 750words & Cognitive Bias Codex)
* **Timespan:** 2010 – Present (15+ years)
* **Emotional & Psychological Core:** Daily self-inquiries, the *Belief Book*, and retrospective tracking of *"Things I used to believe that I no longer believe."*

---

## 📜 Historical Single-Author Complete Diary Datasets (Public Domain)

For long-term longitudinal datasets spanning historical crises and complete lifetimes:

### 1. [philgyford/pepysdiary](https://github.com/philgyford/pepysdiary) (Samuel Pepys: 1660–1669)
* **Format:** Complete day-by-day GitHub repo / database of 10 consecutive years of raw diary entries.
* **Emotional Core:** The quintessential historical lifelog:
  * **Acute existential fear:** Daily death counts and emotional panic during the Great Plague of London (1665).
  * **Crisis & Trauma:** Panic during the Great Fire of London (1666), burying valuables in his garden.
  * **Daily Vulnerability:** Marital fights, jealousy, career ambition, and severe health anxiety (surviving bladder stone surgery without anesthesia).

### 2. Marcus Aurelius — *Meditations* (170–180 AD)
* **Format:** 12 books of private notes written to himself during war and the Antonine Plague.
* **Emotional Core:** Pure real-time cognitive reframing: overcoming anger at untrustworthy subordinates, coping with physical exhaustion, confronting mortality, and active emotional regulation.

### 3. Leo Tolstoy's Diaries (1847–1910 — 63 Continuous Years)
* **Format:** 63 continuous years from age 18 to his death at 82 (available via Project Gutenberg / Open Corpora).
* **Emotional Core:** One of the longest personal psychological logs in history: agonizing self-criticism, creative torment during *War and Peace*, marriage breakdown, and late-life spiritual crisis.

### 4. Franz Kafka's Diaries (1910–1923)
* **Format:** 13 years of raw psychological stream-of-consciousness.
* **Emotional Core:** Severe creative blocks, feelings of social and familial alienation, insomnia, and the perpetual struggle between artistic compulsion and self-doubt.

### 5. Virginia Woolf — *A Writer's Diary* (1918–1941)
* **Format:** 23 years of continuous private journaling.
* **Emotional Core:** The manic highs and paralyzing depressive crashes of the creative cycle, dread of criticism, aging, and surviving the London Blitz.

---

## 🔬 AI Analysis Framework: Tracking Emotional Evolution

When analyzing these single-author corpora with an LLM agent, run the following longitudinal extraction pipeline across chronological epochs (e.g. quarterly or yearly slices):

```
┌───────────────────────────────────────────────────────────┐
│              LONGITUDINAL EXTRACTION PIPELINE             │
├───────────────────────────────────────────────────────────┤
│ 1. Emotional Baseline:                                     │
│    Identify the dominant emotional state (e.g., anxiety,  │
│    striving, grief, flow, contentment).                   │
│                                                           │
│ 2. Crisis & Pivot Identification:                         │
│    What acute failure or crisis forced a change in        │
│    belief or behavior?                                    │
│                                                           │
│ 3. Reframing Half-Life:                                   │
│    How long did it take the author to reframe the event?   │
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

---

## 🔗 Related Notes
- [[public/2026-08-27 what an AI buddy actually needs|what an AI buddy actually needs]] — how longitudinal episodic memory and living user profiles enable genuine AI thought partnership
- [[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]] — memory reconsolidation, emotional amygdala weighting, and sleep consolidation
- [[public/skills/private-to-public-note-promotion/SKILL|private to public note promotion]] — safety rules and procedures for public note releases
